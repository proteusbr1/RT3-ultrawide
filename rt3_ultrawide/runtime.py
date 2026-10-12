"""One reversible Frida session per game; no executable or save-file patches."""
from contextlib import ExitStack, contextmanager
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import frida

from .config import WRAPPER_SHA256, validate_resolution
from .install import STATE, atomic_write, check_game, digest, prepare_launch
from .menu import installed_metadata
from .loading import installed_metadata as installed_loading_metadata
from .museum import prepare as prepare_museum
from .controls import enabled as mouse_shortcuts_enabled

PROBE = """
let unpacked=false;
rpc.exports={
 path(){return Process.getModuleByName('RT3.exe').path;},
 mode(){
  const m=Process.getModuleByName('RT3.exe');
  if(!m.base.equals(ptr('0x400000')))throw Error('Unsupported image base');
  // This instruction is deliberately replaced after the patch attaches.
  // Check unpacking once; do not mistake our own hook for a resolution change.
  if(!unpacked){if(ptr('0x538b60').readU32()!==0xf18b5651)return null;unpacked=true;}
  const r=ptr('0x6d4024').readPointer();if(r.isNull())return null;
  if(ptr('0x6d401c').readPointer().isNull())return null;
  const modes=r.add(0x34).readPointer();if(modes.isNull())return null;
  const index=r.add(0x11421e).readU32();if(index>4096)return null;
  const p=modes.add(index*21),width=p.readU32(),height=p.add(4).readU32();
  return width>=640 && height>=480?[width,height]:null;
 }
};
"""


def processes():
    return [p for p in frida.get_local_device().enumerate_processes() if p.name.lower() == "rt3.exe"]


def process_token(pid):
    """PID plus Windows creation time, so a reused PID is a fresh process."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    times = [wintypes.FILETIME() for _ in range(4)]
    try:
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        return {"pid": pid, "created": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime}
    finally:
        kernel.CloseHandle(handle)


def reserve_session(folder, token):
    """Never inject twice into the same RT3 lifetime, even after an error/stop."""
    path = folder / "session.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous == token:
            raise RuntimeError("This game session already used the helper. Close RT3 and launch it again; "
                               "reattaching to the same process can crash the game.")
    atomic_write(path, json.dumps(token).encode())


@contextmanager
def exclusive_lock(path):
    import msvcrt
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError("An ultrawide helper is already running. Do not attach a second copy.") from error
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def run(game):
    game = check_game(game)
    if digest((game / "D3D8.dll").read_bytes()) != WRAPPER_SHA256:
        raise ValueError("Unsupported D3D8.dll; no runtime patch applied.")
    folder = game / STATE
    ready_file = folder / "ready.json"
    with ExitStack() as stack:
        stack.enter_context(exclusive_lock(folder / "runtime.lock"))
        # Cooperate with the older development launcher when upgrading locally.
        legacy = game / "RT3DisplayFix/prototype/runtime.lock"
        if legacy.exists():
            stack.enter_context(exclusive_lock(legacy))
        ready_file.unlink(missing_ok=True)
        (folder / "STOP").unlink(missing_ok=True)
        candidates = processes()
        if len(candidates) != 1:
            raise RuntimeError("Exactly one running RT3.exe is required.")
        museum = prepare_museum(game)
        token = process_token(candidates[0].pid)
        reserve_session(folder, token)
        session = frida.attach(candidates[0].pid)
        stopped = threading.Event()
        ready = threading.Event()
        errors = []
        script = None

        def detached(reason, crash):
            logging.info("Detached: %s; crash=%s", reason, bool(crash))
            stopped.set()

        def message(event, _data):
            logging.info("%s", json.dumps(event))
            if event.get("type") == "error":
                errors.append(event)
                stopped.set()
            if event.get("type") == "send" and event.get("payload", {}).get("ready"):
                ready.set()

        session.on("detached", detached)
        try:
            probe = session.create_script(PROBE)
            probe.load()
            actual = Path(probe.exports_sync.path()).resolve()
            if os.path.normcase(str(actual)) != os.path.normcase(str(game / "RT3.exe")):
                raise RuntimeError("Running RT3 belongs to another installation.")
            deadline = time.monotonic() + 60
            mode = None
            while time.monotonic() < deadline and not stopped.is_set():
                try:
                    mode = probe.exports_sync.mode()
                except frida.core.RPCException:
                    mode = None
                if mode:
                    break
                stopped.wait(0.25)
            if not mode:
                raise TimeoutError("Game renderer did not become ready within 60 seconds.")
            width, height = mode
            validate_resolution(width, height)
            scale = (height * 4 / 3) / width
            source = (Path(__file__).parent / "assets/ultrawide.js").read_text(encoding="utf-8")
            museum_source = (Path(__file__).parent / "assets/museum.js").read_text(encoding="utf-8")
            controls_source = (Path(__file__).parent / "assets/controls.js").read_text(encoding="utf-8")
            menu = installed_metadata(game)
            loading = installed_loading_metadata(game)
            script = session.create_script(f"const SCALE_X={scale!r};\nconst MENU_ART={json.dumps(menu)};\n"
                                           f"const LOADING_ART={json.dumps(loading)};\n"
                                           f"const MUSEUM_ART={json.dumps(museum)};\n"
                                           f"const MOUSE_SHORTCUTS={json.dumps(mouse_shortcuts_enabled(game))};\n"
                                           + controls_source + "\n" + museum_source + "\n" + source)
            script.on("message", message)
            script.load()
            if not ready.wait(5) or errors:
                raise RuntimeError("Patch failed its startup checks; see the runtime log.")
            atomic_write(ready_file, json.dumps({"helper_pid": os.getpid(), "game_pid": candidates[0].pid,
                                                "game_token": token, "helper_token": process_token(os.getpid()),
                                                "mode": mode}).encode())
            logging.info("Ready: %sx%s, game PID %s", width, height, candidates[0].pid)
            unavailable_since = None
            while not stopped.wait(0.5) and not (folder / "STOP").exists():
                current_mode = probe.exports_sync.mode()
                # The renderer can be unavailable during teardown or transitions.
                # A missing mode is not evidence that the display size changed.
                if current_mode is None:
                    if unavailable_since is None:
                        unavailable_since = time.monotonic()
                    if time.monotonic() - unavailable_since > 10:
                        raise RuntimeError("Renderer remained unavailable for 10 seconds. Relaunch the game.")
                    continue
                unavailable_since = None
                if current_mode != mode:
                    raise RuntimeError(f"Resolution changed from {mode} to {current_mode}. "
                                       "Exit and relaunch to realign the UI and mouse.")
                if (folder / "INSPECT").exists():
                    report = script.exports_sync.inspect()
                    report["stats"] = script.exports_sync.stats()
                    atomic_write(folder / "layout.json", json.dumps(report, indent=2).encode())
                    (folder / "INSPECT").unlink()
            if errors:
                raise RuntimeError("A runtime hook reported an error. Patch detached.")
        finally:
            if script is not None:
                try:
                    script.exports_sync.restore()
                except (frida.InvalidOperationError, frida.core.RPCException):
                    pass
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass
            ready_file.unlink(missing_ok=True)


def launch(game):
    game = check_game(game)
    folder = game / STATE
    candidates = processes()
    if len(candidates) == 1:
        try:
            ready = json.loads((folder / "ready.json").read_text(encoding="utf-8"))
            if (ready.get("game_token") == process_token(candidates[0].pid)
                    and ready.get("helper_token") == process_token(ready["helper_pid"])):
                return "Ultrawide is already active. Changed preferences apply after restarting RT3."
        except (OSError, ValueError, KeyError):
            pass
    if not processes():
        prepare_launch(game)
        os.startfile("steam://rungameid/7610")
        deadline = time.monotonic() + 60
        while not processes():
            if time.monotonic() > deadline:
                raise TimeoutError("Steam did not start RT3. Open Steam, then try again.")
            time.sleep(0.5)
    folder = game / STATE
    folder.mkdir(exist_ok=True)
    command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, "-m", "rt3_ultrawide"]
    log = folder / ("runtime-" + time.strftime("%Y%m%d-%H%M%S") + ".log")
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command + ["runtime", "--game", str(game)], cwd=game,
                                   stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic() + 75
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Runtime could not attach. See " + str(log))
        try:
            if json.loads((folder / "ready.json").read_text())["helper_pid"] == process.pid:
                return "Ultrawide is active. WASD moves the camera; Space pauses. Log: " + str(log)
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.25)
    raise TimeoutError("Runtime readiness timed out. See " + str(log))
