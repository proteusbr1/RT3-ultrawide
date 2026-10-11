"""Validated installation, local backups, and conservative restoration."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import uuid
import zipfile

from . import __version__
from .config import (ARCHIVE_SHA256, CPL_SHA256, ENGINE, EXE_SHA256, HOTKEYS, WRAPPER_SHA256,
                     UPGRADE_WRAPPER_SHA256, UPGRADE_CPL_SHA256,
                     WRAPPER_URL, engine_config, hotkey_config, wrapper_config)

STATE = "RT3Ultrawide"
ALLOWED = {ENGINE, HOTKEYS, "dgVoodoo.conf", "D3D8.dll", "dgVoodooCpl.exe",
           "Launch RT3 Ultrawide.cmd", f"{STATE}/launch.ps1"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_file(game, relative):
    if relative not in ALLOWED:
        raise ValueError(f"Unexpected manifest path: {relative}")
    target = game / relative
    if not target.resolve().is_relative_to(game.resolve()):
        raise ValueError(f"Configuration path escapes the game folder: {relative}")
    return target


def check_game(game):
    game = Path(game).resolve()
    if digest((game / "RT3.exe").read_bytes()) != EXE_SHA256:
        raise ValueError("Unsupported RT3.exe. This release supports only the documented Steam executable hash.")
    if not (game / STATE).resolve().is_relative_to(game):
        raise ValueError("RT3Ultrawide must not be a link outside the game folder.")
    return game


def require_closed():
    import frida
    if any(p.name.lower() == "rt3.exe" for p in frida.get_local_device().enumerate_processes()):
        raise RuntimeError("Save your game and exit Railroad Tycoon 3 first. No configuration files were changed.")


def wrapper_files(archive=None):
    bundled = Path(__file__).parent / "vendor/dgVoodoo2_87_5.zip"
    if archive is None and bundled.exists():
        archive = bundled.read_bytes()
    if archive is None:
        request = urllib.request.Request(WRAPPER_URL, headers={"User-Agent": "RT3-ultrawide/" + __version__})
        with urllib.request.urlopen(request, timeout=90) as response:
            archive = response.read(32 * 1024 * 1024 + 1)
    if digest(archive) != ARCHIVE_SHA256:
        raise ValueError("dgVoodoo download checksum mismatch. Nothing installed.")
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        dll = bundle.read("MS/x86/D3D8.dll")
        config = bundle.read("dgVoodoo.conf")
        cpl = bundle.read("dgVoodooCpl.exe")
    if digest(dll) != WRAPPER_SHA256:
        raise ValueError("Unexpected D3D8.dll checksum.")
    if digest(cpl) != CPL_SHA256:
        raise ValueError("Unexpected dgVoodooCpl.exe checksum.")
    return dll, config, cpl


def manifest_path(game):
    return game / STATE / "installation.json"


def read_manifest(game):
    if not (game / STATE).resolve().is_relative_to(game.resolve()):
        raise ValueError("Installation state must remain inside the game folder.")
    manifest = json.loads(manifest_path(game).read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise ValueError("Unsupported installation manifest.")
    for name, entry in manifest["files"].items():
        safe_file(game, name)
        if entry["backup"]:
            path = (game / STATE / entry["backup"]).resolve()
            if not path.is_relative_to((game / STATE / "backups").resolve()):
                raise ValueError("Unsafe backup path in installation manifest.")
    return manifest


def write_manifest(game, manifest):
    atomic_write(manifest_path(game), (json.dumps(manifest, indent=2) + "\n").encode())


def apply_files(game, files, width, height):
    """Preserve the first baseline; roll back every write if a later write fails."""
    previous = manifest_path(game).read_bytes() if manifest_path(game).exists() else None
    manifest = read_manifest(game) if previous else {"schema": 1, "files": {}}
    current = {name: safe_file(game, name).read_bytes() if safe_file(game, name).exists() else None for name in files}
    generation = uuid.uuid4().hex
    for name, data in files.items():
        if name not in manifest["files"]:
            backup = f"backups/{generation}/{name}" if current[name] is not None else None
            if backup:
                atomic_write(game / STATE / backup, current[name])
            manifest["files"][name] = {"backup": backup, "original_sha256": digest(current[name]) if backup else None}
        manifest["files"][name]["installed_sha256"] = digest(data)
    manifest.update(version=__version__, width=width, height=height, status="installing")
    # A journal exists before writes, including after an unexpected shutdown.
    write_manifest(game, manifest)
    changed = []
    try:
        for name, data in files.items():
            atomic_write(safe_file(game, name), data)
            changed.append(name)
            if digest(safe_file(game, name).read_bytes()) != digest(data):
                raise OSError(f"Read-back verification failed: {name}")
        manifest["status"] = "installed"
        write_manifest(game, manifest)
    except Exception:
        for name in reversed(changed):
            if current[name] is None:
                safe_file(game, name).unlink(missing_ok=True)
            else:
                atomic_write(safe_file(game, name), current[name])
        if previous is None:
            manifest_path(game).unlink(missing_ok=True)
        else:
            atomic_write(manifest_path(game), previous)
        raise


def launcher_files(game):
    if getattr(sys, "frozen", False):
        source = Path(sys.executable).parent
        destination = game / STATE / "app"
        if source.resolve() != destination.resolve():
            if destination.resolve().is_relative_to(source.resolve()):
                raise ValueError("Extract the release outside the game folder before installing.")
            shutil.copytree(source, destination, dirs_exist_ok=True)
        command = [str(destination / Path(sys.executable).name)]
    else:
        # Source installs remain tied to their Python environment and checkout.
        command = [sys.executable, "-m", "rt3_ultrawide"]
    quote = lambda text: "'" + str(text).replace("'", "''") + "'"
    script = "$ErrorActionPreference = 'Stop'\r\n"
    script += "& " + " ".join(quote(c) for c in command + ["launch", "--game", str(game)]) + "\r\n"
    script += "if ($LASTEXITCODE -ne 0) { Read-Host 'Press Enter to close' }\r\n"
    batch = '@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RT3Ultrawide\\launch.ps1"\r\n'
    return {"Launch RT3 Ultrawide.cmd": batch.encode("ascii"),
            f"{STATE}/launch.ps1": b"\xef\xbb\xbf" + script.encode("utf-8")}


def install(game, width, height, archive=None):
    game = check_game(game)
    require_closed()
    engine = engine_config(safe_file(game, ENGINE).read_bytes(), width, height)
    hotkeys = hotkey_config(safe_file(game, HOTKEYS).read_bytes())
    dll_path = safe_file(game, "D3D8.dll")
    if dll_path.exists() and digest(dll_path.read_bytes()) not in {WRAPPER_SHA256, UPGRADE_WRAPPER_SHA256}:
        raise ValueError("A different D3D8.dll is already installed. Back it up and remove it before installing this patch.")
    config_path = safe_file(game, "dgVoodoo.conf")
    cpl_path = safe_file(game, "dgVoodooCpl.exe")
    if cpl_path.exists() and digest(cpl_path.read_bytes()) not in {CPL_SHA256, UPGRADE_CPL_SHA256}:
        raise ValueError("A different dgVoodooCpl.exe is installed. Back it up and remove it before installing.")
    dll, default_config, cpl = wrapper_files(archive)
    config = config_path.read_bytes() if config_path.exists() else default_config
    files = {ENGINE: engine, HOTKEYS: hotkeys, "D3D8.dll": dll, "dgVoodooCpl.exe": cpl,
             "dgVoodoo.conf": wrapper_config(config, width, height)}
    files.update(launcher_files(game))
    require_closed()
    apply_files(game, files, width, height)
    return "Installed. Start the game with 'Launch RT3 Ultrawide.cmd' in the game folder."


def prepare_launch(game):
    game = check_game(game)
    require_closed()
    manifest = read_manifest(game)
    if manifest["status"] != "installed":
        raise ValueError("Installation is incomplete. Reinstall or restore backups first.")
    if digest((game / "D3D8.dll").read_bytes()) != WRAPPER_SHA256:
        raise ValueError("D3D8.dll has changed. Reinstall the supported wrapper.")
    width, height = manifest["width"], manifest["height"]
    # RT3 saves its temporary windowed flag on exit. Restore startup mode each launch.
    apply_files(game, {ENGINE: engine_config((game / ENGINE).read_bytes(), width, height),
                      "dgVoodoo.conf": wrapper_config((game / "dgVoodoo.conf").read_bytes(), width, height)}, width, height)
    return game


def uninstall(game, preserve_changed=False):
    game = Path(game).resolve()
    require_closed()
    manifest = read_manifest(game)
    actions = {}
    changed = []
    for name, entry in manifest["files"].items():
        target = safe_file(game, name)
        current = target.read_bytes() if target.exists() else None
        backup = game / STATE / entry["backup"] if entry["backup"] else None
        original = backup.read_bytes() if backup else None
        if original is not None and digest(original) != entry["original_sha256"]:
            raise ValueError(f"Backup checksum mismatch: {name}. Nothing restored.")
        if current == original:
            continue
        if current is not None and digest(current) != entry["installed_sha256"]:
            changed.append(name)
        actions[name] = original
    if changed and not preserve_changed:
        raise ValueError("Files changed since installation: " + ", ".join(changed) +
                         ". Use --preserve-changed to keep a separate copy and restore the original baseline.")
    # Always retain the complete current state before restoring any file.
    generation = "before-restore-" + uuid.uuid4().hex
    for name in actions:
        target = safe_file(game, name)
        if target.exists():
            atomic_write(game / STATE / "backups" / generation / name, target.read_bytes())
    completed = []
    try:
        for name, data in actions.items():
            target = safe_file(game, name)
            if data is None:
                target.unlink(missing_ok=True)
            else:
                atomic_write(target, data)
            completed.append(name)
        manifest["status"] = "uninstalled"
        write_manifest(game, manifest)
    except Exception:
        for name in reversed(completed):
            current_backup = game / STATE / "backups" / generation / name
            if current_backup.exists():
                atomic_write(safe_file(game, name), current_backup.read_bytes())
            else:
                safe_file(game, name).unlink(missing_ok=True)
        raise
    return "Original files restored. Backup history and the inactive helper remain in RT3Ultrawide."
