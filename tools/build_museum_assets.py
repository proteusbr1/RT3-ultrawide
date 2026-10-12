"""Convert the generated museum plates to losslessly packed runtime textures.

The supplied paintings are 1942x809. The 3840x1600 export is a resample, not
native 4K generated detail. No original Bink movie is edited or redistributed.
"""
import hashlib
import json
from pathlib import Path
import zlib

from PIL import Image

ASSETS = Path(__file__).resolve().parents[1] / "rt3_ultrawide/assets"


def main():
    rooms = []
    for letter in "abcd":
        source = Image.open(ASSETS / f"museum-{letter}.png").convert("RGBA")
        image = source.resize((3840, 1600), Image.Resampling.LANCZOS)
        texture = Image.new("RGBA", (4096, 2048), (0, 0, 0, 255))
        texture.paste(image, (0, 0))
        raw = texture.tobytes("raw", "BGRA")
        packed = zlib.compress(raw, 9)
        filename = f"museum-{letter}.bgra.zlib"
        (ASSETS / filename).write_bytes(packed)
        rooms.append({"room": letter.upper(), "file": filename,
                      "source_size": list(source.size), "image_width": 3840,
                      "image_height": 1600, "texture_width": 4096, "texture_height": 2048,
                      "sha256": hashlib.sha256(packed).hexdigest(),
                      "raw_sha256": hashlib.sha256(raw).hexdigest()})
    (ASSETS / "museum-artwork.json").write_text(json.dumps({"schema": 1, "rooms": rooms}, indent=2) + "\n")


if __name__ == "__main__":
    main()
