import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from archive_fixture import combined_archive
from rt3_ultrawide import loading, menu


class LoadingArtworkTests(unittest.TestCase):
    def test_loading_upgrade_preserves_menu_directory_and_unrelated_data(self):
        installed = combined_archive() + b"UNRELATED GAME DATA"
        original, hashes = bytearray(installed), {}
        for name, (start, end) in loading.entries(installed).items():
            original[start + 128] ^= 255
            hashes[name] = hashlib.sha256(original[start:end]).hexdigest()
        with patch.object(loading, "ORIGINAL_HASHES", hashes):
            result = loading.patch_archive(original)
        self.assertEqual(result, installed)
        self.assertEqual(loading.patch_archive(result), result)
        self.assertEqual(menu.patch_archive(result), result)

    def test_original_partial_and_complete_install_detection(self):
        original, hashes = bytearray(loading.archive_bytes()), {}
        for name, (start, end) in loading.entries(original).items():
            original[start + 128] ^= 255
            hashes[name] = hashlib.sha256(original[start:end]).hexdigest()
        with tempfile.TemporaryDirectory() as folder, patch.object(loading, "ORIGINAL_HASHES", hashes):
            target = Path(folder) / menu.MENU_ARCHIVE
            target.parent.mkdir(parents=True)
            target.write_bytes(original)
            self.assertIsNone(loading.installed_metadata(folder))
            start, _ = next(iter(loading.entries(original).values()))
            original[start + 128] ^= 255
            target.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "partially installed"):
                loading.installed_metadata(folder)
            target.write_bytes(loading.patch_archive(original))
            self.assertEqual(loading.installed_metadata(folder), loading.metadata())

    def test_unknown_loading_texture_is_rejected_before_install(self):
        data = bytearray(loading.archive_bytes())
        start, _ = next(iter(loading.entries(data).values()))
        data[start + 128] ^= 255
        with self.assertRaisesRegex(ValueError, "Unknown loading texture"):
            loading.patch_archive(data)

    def test_all_variants_have_complete_texture_levels_and_visible_bounds(self):
        data, info = loading.archive_bytes(), loading.metadata()
        self.assertEqual(len(info["variants"]), 6)
        self.assertEqual(len(loading.entries(data)), 36)
        for name, (start, end) in loading.entries(data).items():
            level = ord(name[-5]) - ord("A")
            dds = data[start:end]
            self.assertEqual(dds[:4], b"DDS ")
            self.assertEqual(struct.unpack_from("<II", dds, 12), (1024 >> level, 2048 >> level))
        for art in info["variants"]:
            self.assertLessEqual(art["image_width"], art["texture_width"])
            self.assertLessEqual(art["image_height"], art["texture_height"])
        spans = loading.entries(data)
        a, b = spans["loadscreen_A.dds"]
        c, d = spans["loadscreen5_A.dds"]
        self.assertEqual(data[a:b], data[c:d])


if __name__ == "__main__":
    unittest.main()
