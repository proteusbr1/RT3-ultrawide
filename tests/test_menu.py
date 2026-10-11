import hashlib
import struct
import unittest
from unittest.mock import patch

from rt3_ultrawide import menu


class MenuArchiveTests(unittest.TestCase):
    def test_only_menu_payloads_change_and_repeat_install_is_identical(self):
        bundled = menu.archive_bytes()
        original = bytearray(bundled)
        expected = {}
        for name, (start, end) in menu.menu_entries(bundled).items():
            original[start + 128] ^= 255
            expected[name] = hashlib.sha256(original[start:end]).hexdigest()
        original.extend(b"UNRELATED TRAILING GAME DATA")
        with patch.object(menu, "ORIGINAL_HASHES", expected):
            output = menu.patch_archive(bytes(original))
        self.assertEqual(output, bundled + b"UNRELATED TRAILING GAME DATA")
        self.assertEqual(menu.patch_archive(output), output)

    def test_unknown_menu_pixels_are_rejected(self):
        data = bytearray(menu.archive_bytes())
        start, _ = next(iter(menu.menu_entries(data).values()))
        data[start + 128] ^= 255
        with self.assertRaisesRegex(ValueError, "Unknown menu texture"):
            menu.patch_archive(data)

    def test_bad_bounds_and_overlapping_entries_are_rejected(self):
        source = menu.archive_bytes()
        for offset, value, message in [(8 + 8, len(source), "bounds"), (8 + 74 + 8, 0, "Overlapping")]:
            data = bytearray(source)
            struct.pack_into("<I", data, offset, value)
            with self.assertRaisesRegex(ValueError, message):
                menu.menu_entries(data)

    def test_texture_storage_contains_visible_art_without_uv_overflow(self):
        info = menu.metadata()
        self.assertLessEqual(info["image_width"], info["texture_width"])
        self.assertLessEqual(info["image_height"], info["texture_height"])
        data = menu.archive_bytes()
        for level, (start, end) in enumerate(menu.menu_entries(data).values()):
            dds = data[start:end]
            self.assertEqual(dds[:4], b"DDS ")
            height, width = struct.unpack_from("<II", dds, 12)
            self.assertEqual((width, height), (2048 >> level, 1024 >> level))


if __name__ == "__main__":
    unittest.main()
