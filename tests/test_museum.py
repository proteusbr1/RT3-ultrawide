import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from rt3_ultrawide import museum


class MuseumTests(unittest.TestCase):
    def test_all_four_payloads_have_valid_bgra_and_opaque_visible_pixels(self):
        for room in museum.metadata()["rooms"]:
            with self.subTest(room=room["room"]):
                raw = museum.unpack(room)
                self.assertEqual(len(raw), 4096 * 2048 * 4)
                self.assertEqual(raw[3::4], b"\xff" * (4096 * 2048))
                self.assertNotEqual(raw[:3840 * 4], b"\0\0\0\xff" * 3840)

    def test_path_traversal_and_incomplete_metadata_rejected(self):
        value = museum.metadata()
        with tempfile.TemporaryDirectory() as folder, patch.object(museum, "ASSETS", Path(folder)):
            file = Path(folder) / "museum-artwork.json"
            value["rooms"][0]["file"] = "../outside.zlib"
            file.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "path"):
                museum.metadata()
            value["rooms"].pop()
            file.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                museum.metadata()

    def test_corrupt_and_oversize_payload_rejected(self):
        room = museum.metadata()["rooms"][0]
        with tempfile.TemporaryDirectory() as folder, patch.object(museum, "ASSETS", Path(folder)):
            target = Path(folder) / room["file"]
            target.write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "checksum"):
                museum.unpack(room)
            packed = zlib.compress(b"a" * 9)
            target.write_bytes(packed)
            room["sha256"] = hashlib.sha256(packed).hexdigest()
            with patch.object(museum, "RAW_SIZE", 8), self.assertRaisesRegex(ValueError, "payload"):
                museum.unpack(room)

    def test_original_movie_opt_out_creates_no_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            (game / "RT3Ultrawide").mkdir()
            (game / "RT3Ultrawide/ORIGINAL_MUSEUM").touch()
            self.assertIsNone(museum.prepare(game))
            self.assertFalse((game / "RT3Ultrawide/museum-cache").exists())


if __name__ == "__main__":
    unittest.main()
