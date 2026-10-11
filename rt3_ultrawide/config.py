"""Small, lossless transformations of the user's own configuration files."""
import re
import struct

EXE_SHA256 = "c6e178bfc694b5fc5e059a584fc84045627cb3613604c83e19ba1906ccc0d252"
WRAPPER_SHA256 = "d03e2562178db1fcf3493fc0a0b23a465e35c55d73adb3ec095be866cd662704"
CPL_SHA256 = "87fb878166dcaef3e75ff170de030527c73f5c9b164c5943da13f8a97b0b75c6"
UPGRADE_WRAPPER_SHA256 = "2fe0314195d0caf2c72c5496352c4235858b0f104a3a2b0d88832f15f76faf57"
UPGRADE_CPL_SHA256 = "ebecc6dc72f9a43146ec5954564a47ac68f9da51fa692cfc64fce553dd1e9a6d"
ARCHIVE_SHA256 = "5ffde6927f7355ca3fdd5d785b581256a8e6539fa13e395a891ade6ba1040850"
WRAPPER_URL = "https://github.com/dege-diosg/dgVoodoo2/releases/download/v2.87.5/dgVoodoo2_87_5.zip"
ENGINE = "Data/Configuration/engine.cfg"
HOTKEYS = "HotKeys/hotkeys.txt"
BINDINGS = {
    "Camera Forward": "W", "Camera Backward": "S",
    "Camera Left": "A", "Camera Right": "D",
    "Pause Game (Toggle On/Off)": "Space",
    "Go to Chat in multi-player": "CTRL+Space",
    "Current train whistles": "SHIFT+W", "Last dialog": "SHIFT+D",
    "Ledger - Game Status": "SHIFT+A", "Station list": "CTRL+F",
}


def validate_resolution(width, height):
    if not (1280 <= width <= 8192 and 720 <= height <= 4320
            and 16 / 9 - 0.001 <= width / height <= 32 / 9 + 0.001):
        raise ValueError("Choose a landscape resolution between 16:9 and 32:9, at least 1280x720.")


def engine_config(data, width, height):
    validate_resolution(width, height)
    if len(data) < 17 or struct.unpack_from("<I", data)[0] != 1051:
        raise ValueError("Unsupported engine.cfg. Start the supported game once, then exit.")
    result = bytearray(data)
    struct.pack_into("<II", result, 4, width, height)
    # Start a full-resolution device; the runtime switches only the focus/input flag.
    result[16] = 1
    return bytes(result)


def ini_value(text, section, key, value):
    newline = "\r\n" if "\r\n" in text else "\n"
    pattern = re.compile(r"(?ms)^\[" + re.escape(section) + r"\][ \t]*\r?\n.*?(?=^\[|\Z)")
    blocks = list(pattern.finditer(text))
    if len(blocks) > 1:
        raise ValueError(f"Duplicate configuration section: {section}")
    if not blocks:
        return text.rstrip("\r\n") + newline * 2 + f"[{section}]" + newline + f"{key} = {value}" + newline
    block = blocks[0]
    key_pattern = re.compile(r"(?m)^([ \t]*" + re.escape(key) + r"[ \t]*=)[^\r\n]*")
    if len(key_pattern.findall(block[0])) > 1:
        raise ValueError(f"Duplicate configuration key: {section}/{key}")
    replacement, count = key_pattern.subn(lambda m: m[1] + " " + value, block[0])
    if not count:
        replacement = replacement.rstrip("\r\n") + newline + f"{key} = {value}" + newline + newline
    return text[:block.start()] + replacement + text[block.end():]


def wrapper_config(data, width, height):
    validate_resolution(width, height)
    # Upstream 2.87.5 ships CR CR LF; normalize before locating INI sections.
    text = data.decode("latin-1").replace("\r\r\n", "\r\n")
    options = {
        "General": {"FullScreenMode": "false", "ScalingMode": "centered_ar",
                    "CenterAppWindow": "true", "CaptureMouse": "true"},
        "GeneralExt": {"WindowedAttributes": "borderless, fullscreensize"},
        "DirectX": {"Resolution": f"h:{width}, v:{height}", "AppControlledScreenMode": "false",
                    "DisableAltEnterToToggleScreenMode": "true", "dgVoodooWatermark": "false"},
        "DirectXExt": {"ExtraEnumeratedResolutions": f"{width}x{height}"},
    }
    for section, keys in options.items():
        for key, value in keys.items():
            text = ini_value(text, section, key, value)
    return text.encode("latin-1")


def hotkey_config(data):
    text = data.decode("latin-1")
    # Description strings are identifiers understood by the game; keep them intact.
    found = set()
    for description, key in BINDINGS.items():
        pattern = re.compile(r"(?m)^(" + re.escape(description) + r"[ \t]*=)[^\r\n]*")
        text, count = pattern.subn(lambda m: m[1] + " " + key, text)
        if count != 1:
            raise ValueError(f"Missing or duplicate hotkey action: {description}")
        found.add(description)
    targets = {key.upper() for key in BINDINGS.values()}
    for line in text.splitlines():
        if "=" not in line or line.lstrip().startswith(";"):
            continue
        action, key = (part.strip() for part in line.split("=", 1))
        if action not in found and key.upper() in targets:
            raise ValueError(f"Custom hotkey conflict: {action} uses {key}. Reassign it before installing.")
    return text.encode("latin-1")
