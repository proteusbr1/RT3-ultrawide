"""Encode the generated background into RT3's texture override archive.

Requires Pillow for development only. No original game pixels are read or copied.
The directory hashes identify the six existing texture names in the Steam build.
"""
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "rt3_ultrawide/assets"
HASHES = [0xc74cbc6d, 0xe09a4a4b, 0x3bae2696, 0x068db472, 0x2ec76cec, 0x4814fac9]


def main():
    image = Image.open(ASSETS / "menu-background.png").convert("RGBA")
    # Texture padding is storage only; runtime UVs exclude every padded pixel.
    texture = Image.new("RGBA", (2048, 1024))
    texture.paste(image, (0, 0))
    directory, payload, offset = [], [], 0
    for level, identifier in enumerate(HASHES):
        mip = texture.resize((2048 >> level, 1024 >> level), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        mip.save(buffer, format="DDS", pixel_format="DXT5")
        data = buffer.getvalue()
        name = f"Setup_Background_{chr(65 + level)}.dds".encode("ascii")
        directory.append(struct.pack("<IIIB61s", identifier, len(data), offset, 0, name))
        payload.append(data)
        offset += len(data)
    archive = struct.pack("<II", 1003, len(HASHES)) + b"".join(directory + payload)
    (ASSETS / "menu-background.pk4").write_bytes(archive)
    metadata = {"sha256": hashlib.sha256(archive).hexdigest(),
                "image_width": image.width, "image_height": image.height,
                "texture_width": 2048, "texture_height": 1024}
    (ASSETS / "menu-background.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()
