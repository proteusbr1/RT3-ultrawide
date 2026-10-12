"""Persistent, opt-out mouse shortcuts; keyboard bindings live in hotkeys.txt."""
from pathlib import Path


def enabled(game):
    return not (Path(game) / "RT3Ultrawide/NATIVE_MOUSE").exists()


def set_enabled(game, use_shortcuts):
    marker = Path(game) / "RT3Ultrawide/NATIVE_MOUSE"
    if use_shortcuts:
        marker.unlink(missing_ok=True)
    else:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("Mouse shortcuts disabled. Delete this file to enable on next launch.\n", encoding="ascii")
