"""Encode generated loading panoramas into same-size DXT5 texture payloads.

Requires Pillow 12.3.0 for development only. No original game pixels are used.
The original directory identifiers and fingerprints are metadata, not artwork.
"""
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "rt3_ultrawide/assets"
SCENES = ["bridge", "penny", "cab", "station", "yard", "bridge"]


def main():
    originals = json.loads((ASSETS / "loading-originals.json").read_text())
    directory, payload, bounds, offset = [], [], [], 0
    for variant, scene in enumerate(SCENES):
        image = Image.open(ASSETS / f"loading-{scene}.png").convert("RGBA")
        if image.width > 2048 or image.height > 1024:
            raise ValueError("Artwork exceeds texture storage; do not silently distort it.")
        # Preserve the source pixels and exclude padding with per-scene runtime UVs.
        texture = Image.new("RGBA", (2048, 1024))
        texture.paste(image, (0, 0))
        bounds.append({"scene": scene, "image_width": image.width, "image_height": image.height,
                       "texture_width": 2048, "texture_height": 1024})
        for level in range(6):
            mip = texture.resize((2048 >> level, 1024 >> level), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            mip.save(buffer, format="DDS", pixel_format="DXT5")
            data = buffer.getvalue()
            name = f"loadscreen{variant or ''}_{chr(65 + level)}.dds"
            directory.append(struct.pack("<IIIB61s", originals[name]["directory_hash"],
                                         len(data), offset, 0, name.encode("ascii")))
            payload.append(data)
            offset += len(data)
    archive = struct.pack("<II", 1003, len(directory)) + b"".join(directory + payload)
    (ASSETS / "loading-backgrounds.pk4").write_bytes(archive)
    info = {"sha256": hashlib.sha256(archive).hexdigest(), "variants": bounds}
    (ASSETS / "loading-backgrounds.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(info))


if __name__ == "__main__":
    main()
