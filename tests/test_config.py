import struct
import unittest

from rt3_ultrawide.config import BINDINGS, engine_config, hotkey_config, ini_value, wrapper_config


class ConfigurationTests(unittest.TestCase):
    def test_upstream_double_cr_does_not_duplicate_sections(self):
        from rt3_ultrawide.install import wrapper_files
        source = wrapper_files()[1]
        output = wrapper_config(source, 3440, 1440)
        self.assertNotIn(b"\r\r\n", output)
        for section in (b"[General]", b"[GeneralExt]", b"[DirectX]", b"[DirectXExt]"):
            self.assertEqual(output.count(section), 1)
        self.assertEqual(wrapper_config(output, 3440, 1440), output)

    def test_engine_preserves_all_unrelated_bytes(self):
        original = struct.pack("<III", 1051, 1600, 1200) + bytes(range(100))
        actual = engine_config(original, 3440, 1440)
        self.assertEqual(struct.unpack_from("<II", actual, 4), (3440, 1440))
        self.assertEqual(actual[16], 1)
        self.assertEqual(len(actual), len(original))
        for i in range(len(original)):
            if i not in range(4, 12) and i != 16:
                self.assertEqual(actual[i], original[i])

    def test_unsupported_engine_and_resolution_are_rejected(self):
        with self.assertRaises(ValueError):
            engine_config(b"broken", 3440, 1440)
        for width, height in [(800, 600), (1440, 3440), (10000, 1000)]:
            with self.assertRaises(ValueError):
                engine_config(struct.pack("<I", 1051) + bytes(30), width, height)

    def test_ini_preserves_unrelated_sections_and_crlf(self):
        source = b"Version = 0x287\r\n[General]\r\n; keep\r\nGamma = 42\r\n[DirectX]\r\nResolution = unforced\r\n"
        output = wrapper_config(source, 3440, 1440)
        self.assertIn(b"; keep\r\nGamma = 42\r\n", output)
        self.assertIn(b"Resolution = h:3440, v:1440\r\n", output)
        self.assertIn(b"dgVoodooWatermark = false", output)
        self.assertEqual(wrapper_config(output, 3440, 1440), output)
        self.assertNotIn(b"\n", output.replace(b"\r\n", b""))

    def test_duplicate_sections_and_keys_are_rejected(self):
        for text in ["[General]\nx=1\n[General]\nx=2\n", "[General]\nx=1\nx=2\n"]:
            with self.assertRaises(ValueError):
                ini_value(text, "General", "x", "3")

    def test_hotkeys_preserve_custom_unrelated_action(self):
        source = "\r\n".join(f"{name} = F12" for name in BINDINGS) + "\r\nCustom unrelated action = CTRL+Q\r\n"
        result = hotkey_config(source.encode())
        self.assertIn(b"Custom unrelated action = CTRL+Q\r\n", result)
        self.assertIn(b"Pause Game (Toggle On/Off) = Space", result)
        self.assertEqual(hotkey_config(result), result)

    def test_hotkey_conflict_and_missing_action_are_rejected(self):
        source = "\n".join(f"{name} = F12" for name in BINDINGS)
        with self.assertRaisesRegex(ValueError, "conflict"):
            hotkey_config((source + "\nCustom action = W").encode())
        with self.assertRaisesRegex(ValueError, "Missing"):
            hotkey_config(b"Camera Forward = Up Arrow")


if __name__ == "__main__":
    unittest.main()
