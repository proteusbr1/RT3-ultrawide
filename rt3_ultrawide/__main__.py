"""Command-line interface and double-click GUI entry point."""
import argparse
import json
import logging
from pathlib import Path
import sys

from . import __version__


def doctor(game):
    from .config import ENGINE, EXE_SHA256, HOTKEYS, WRAPPER_SHA256
    from .install import digest
    import frida
    game = Path(game).resolve()
    hashes = {name: digest((game / name).read_bytes()) if (game / name).is_file() else None
              for name in ["RT3.exe", "D3D8.dll"]}
    return {"version": __version__, "frida": frida.__version__,
            "supported_executable": hashes["RT3.exe"] == EXE_SHA256,
            "supported_wrapper": hashes["D3D8.dll"] == WRAPPER_SHA256,
            "hashes": hashes, "engine_config_exists": (game / ENGINE).exists(),
            "hotkeys_exist": (game / HOTKEYS).exists(),
            "runtime_source_exists": (Path(__file__).parent / "assets/ultrawide.js").exists()}


def main():
    parser = argparse.ArgumentParser(description="Railroad Tycoon 3 Ultrawide (experimental)")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    for name in ["install", "launch", "runtime", "doctor", "uninstall", "stop"]:
        command = sub.add_parser(name)
        command.add_argument("--game", type=Path, required=True, help="Folder containing RT3.exe")
        if name == "install":
            command.add_argument("--width", type=int, required=True)
            command.add_argument("--height", type=int, required=True)
        if name == "uninstall":
            command.add_argument("--preserve-changed", action="store_true")
        if name == "doctor":
            command.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command is None:
        from .gui import show
        show()
        return 0
    try:
        from .install import STATE, install, uninstall
        if args.command == "install":
            result = install(args.game, args.width, args.height)
        elif args.command == "uninstall":
            result = uninstall(args.game, args.preserve_changed)
        elif args.command == "doctor":
            result = json.dumps(doctor(args.game), indent=2)
            if args.output:
                args.output.write_text(result + "\n", encoding="utf-8")
        elif args.command == "stop":
            (args.game / STATE / "STOP").touch()
            result = "Requested a clean detach. Relaunch the game to return to its original viewport."
        elif args.command == "launch":
            from .runtime import launch
            result = launch(args.game)
        else:
            from .runtime import run
            folder = args.game / STATE
            folder.mkdir(exist_ok=True)
            logging.basicConfig(filename=folder / "runtime-latest.log", level=logging.INFO,
                                format="%(asctime)s %(levelname)s %(message)s", force=True)
            run(args.game)
            result = "Runtime stopped."
        if sys.stdout is not None:
            print(result)
        return 0
    except Exception as error:
        logging.exception("Operation failed")
        if sys.stderr is not None:
            print(str(error), file=sys.stderr)
        elif args.command != "runtime":
            from tkinter import Tk, messagebox
            root = Tk()
            root.withdraw()
            messagebox.showerror("RT3 Ultrawide", str(error))
            root.destroy()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
