"""Validated replacement of the six loading atlases, including all texture levels."""
import hashlib
import json
from pathlib import Path

from .menu import ASSETS, MENU_ARCHIVE, menu_entries

ORIGINAL_HASHES = {
    name: entry["sha256"] for name, entry in
    json.loads((ASSETS / "loading-originals.json").read_text(encoding="utf-8")).items()
}


def entries(data):
    return menu_entries(data, ORIGINAL_HASHES)


def metadata():
    return json.loads((ASSETS / "loading-backgrounds.json").read_text(encoding="utf-8"))


def archive_bytes():
    data = (ASSETS / "loading-backgrounds.pk4").read_bytes()
    if hashlib.sha256(data).hexdigest() != metadata()["sha256"]:
        raise ValueError("Loading artwork checksum mismatch.")
    return data


def installed_metadata(game):
    path = Path(game) / MENU_ARCHIVE
    if not path.is_file():
        return None
    current, expected = path.read_bytes(), archive_bytes()
    targets, replacements = entries(current), entries(expected)
    matches = []
    for name, (start, end) in targets.items():
        a, b = replacements[name]
        actual = current[start:end]
        matches.append(actual == expected[a:b])
        if not matches[-1] and hashlib.sha256(actual).hexdigest() != ORIGINAL_HASHES[name]:
            raise ValueError(f"Unknown loading texture: {name}. Restore or reinstall a supported game build.")
    if any(matches) and not all(matches):
        raise ValueError("Loading artwork is only partially installed.")
    return metadata() if all(matches) else None


def patch_archive(original):
    replacements = archive_bytes()
    source, target = entries(replacements), entries(original)
    result = bytearray(original)
    for name, (start, end) in target.items():
        a, b = source[name]
        data = replacements[a:b]
        if end - start != len(data):
            raise ValueError("Unexpected loading texture size.")
        current = original[start:end]
        if current != data and hashlib.sha256(current).hexdigest() != ORIGINAL_HASHES[name]:
            raise ValueError(f"Unknown loading texture: {name}. Nothing installed.")
        result[start:end] = data
    return bytes(result)
