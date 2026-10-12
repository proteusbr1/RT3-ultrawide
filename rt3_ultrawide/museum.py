"""Validate and stage optional museum textures without touching original movies."""
import hashlib
import json
from pathlib import Path
import zlib

from .install import atomic_write, check_game, STATE

ASSETS = Path(__file__).parent / "assets"
RAW_SIZE = 4096 * 2048 * 4


def set_style(game, reimagined=True):
    game = check_game(game)
    marker = game / STATE / "ORIGINAL_MUSEUM"
    if reimagined:
        marker.unlink(missing_ok=True)
    else:
        atomic_write(marker, b"Use original museum movies on the next launch.\n")


def metadata():
    value = json.loads((ASSETS / "museum-artwork.json").read_text(encoding="utf-8"))
    if value.get("schema") != 1 or [r.get("room") for r in value.get("rooms", [])] != list("ABCD"):
        raise ValueError("Incomplete museum artwork metadata.")
    for room in value["rooms"]:
        if room["file"] != f"museum-{room['room'].lower()}.bgra.zlib":
            raise ValueError("Unexpected museum asset path.")
        if [room[k] for k in ["image_width", "image_height", "texture_width", "texture_height"]] != [3840, 1600, 4096, 2048]:
            raise ValueError("Unsupported museum texture dimensions.")
    return value


def unpack(room):
    packed = (ASSETS / room["file"]).read_bytes()
    if hashlib.sha256(packed).hexdigest() != room["sha256"]:
        raise ValueError("Museum artwork checksum mismatch.")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, RAW_SIZE + 1)
    if len(raw) != RAW_SIZE or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("Invalid museum texture payload.")
    if hashlib.sha256(raw).hexdigest() != room["raw_sha256"]:
        raise ValueError("Museum pixel checksum mismatch.")
    return raw


def prepare(game):
    # A reversible opt-out, also useful for comparing original animations.
    if (Path(game) / STATE / "ORIGINAL_MUSEUM").exists():
        return None
    value = metadata()
    folder = Path(game) / STATE / "museum-cache"
    if not folder.resolve().is_relative_to((Path(game) / STATE).resolve()):
        raise ValueError("Museum cache must remain inside the mod folder.")
    for room in value["rooms"]:
        target = folder / (room["raw_sha256"] + ".bgra")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != room["raw_sha256"]:
            atomic_write(target, unpack(room))
        room["path"] = str(target.resolve())
    return value
