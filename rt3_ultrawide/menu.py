"""Replace only validated menu texture payloads, retaining every other byte."""
import hashlib
import json
import struct
from pathlib import Path

MENU_ARCHIVE = "Data/2D/rt3_2DDS.PK4"
ASSETS = Path(__file__).parent / "assets"
ORIGINAL_HASHES = dict(zip(
    [f"Setup_Background_{letter}.dds" for letter in "ABCDEF"],
    ["ca498fbddff18bc2307bfd0de5910011101b30e70a91374c7162462c9d8ee864",
     "78c1a669e82e69014000559bba633bec156212352c6491220612a58975a98a14",
     "5503d1a3d8232570b8456829cd23ce9121782b6b41b27fb3f862c8e3c0256948",
     "ebf7510e06aafff00ade584f547b479dd63968a7cf118e4a0ec79f340802e83c",
     "8ff634f4f7142b9bd50614cc0158fee8d6c099f65277295c4f3e304aece82b8c",
     "23edbf68fd293557c93a5e9a3fdd13786506cdf35e4d7bcaae0ffb83f827b398"]))


def menu_entries(data):
    if len(data) < 8:
        raise ValueError("Truncated texture archive.")
    version, count = struct.unpack_from("<II", data)
    base = 8 + 74 * count
    if version != 1003 or base > len(data):
        raise ValueError("Unsupported texture archive directory.")
    result, spans = {}, []
    for index in range(count):
        _, size, offset, flag, raw_name = struct.unpack_from("<IIIB61s", data, 8 + 74 * index)
        name = raw_name.split(b"\0")[0].decode("ascii")
        start, end = base + offset, base + offset + size
        if end > len(data):
            raise ValueError("Texture archive entry exceeds file bounds.")
        spans.append((start, end))
        if name in ORIGINAL_HASHES:
            if name in result or flag != 0:
                raise ValueError("Duplicate or compressed menu texture entry.")
            result[name] = (start, end)
    spans.sort()
    if any(right[0] < left[1] for left, right in zip(spans, spans[1:])):
        raise ValueError("Overlapping texture archive entries.")
    if result.keys() != ORIGINAL_HASHES.keys():
        raise ValueError("Required menu textures are missing.")
    return result


def metadata():
    return json.loads((ASSETS / "menu-background.json").read_text(encoding="utf-8"))


def archive_bytes():
    data = (ASSETS / "menu-background.pk4").read_bytes()
    if hashlib.sha256(data).hexdigest() != metadata()["sha256"]:
        raise ValueError("Menu artwork checksum mismatch.")
    return data


def installed_metadata(game):
    path = Path(game) / MENU_ARCHIVE
    if not path.is_file():
        return None
    current, expected = path.read_bytes(), archive_bytes()
    entries, replacements = menu_entries(current), menu_entries(expected)
    matches = []
    for name, (start, end) in entries.items():
        a, b = replacements[name]
        actual = current[start:end]
        matches.append(actual == expected[a:b])
        if not matches[-1] and hashlib.sha256(actual).hexdigest() != ORIGINAL_HASHES[name]:
            raise ValueError("Unknown menu texture. Restore it or reinstall a supported game build.")
    if any(matches) and not all(matches):
        raise ValueError("Menu artwork is only partially installed.")
    return metadata() if all(matches) else None


def patch_archive(original):
    replacements = archive_bytes()
    source, target = menu_entries(replacements), menu_entries(original)
    result = bytearray(original)
    for name, (start, end) in target.items():
        a, b = source[name]
        data = replacements[a:b]
        if end - start != len(data):
            raise ValueError("Unexpected menu texture size.")
        current = original[start:end]
        if current != data and hashlib.sha256(current).hexdigest() != ORIGINAL_HASHES[name]:
            raise ValueError(f"Unknown menu texture: {name}. Nothing installed.")
        result[start:end] = data
    return bytes(result)
