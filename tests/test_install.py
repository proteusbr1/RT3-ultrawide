import json
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rt3_ultrawide import install as installer
from rt3_ultrawide.config import BINDINGS, CPL_SHA256, ENGINE, HOTKEYS, WRAPPER_SHA256


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name)
        self.path = self.game / "dgVoodoo.conf"
        self.path.write_bytes(b"original")
        self.closed = patch.object(installer, "require_closed")
        self.closed.start()
        self.addCleanup(self.closed.stop)

    def test_original_backup_survives_updates_and_uninstall(self):
        installer.apply_files(self.game, {"dgVoodoo.conf": b"one", "D3D8.dll": b"wrapper"}, 3440, 1440)
        first = installer.read_manifest(self.game)
        installer.apply_files(self.game, {"dgVoodoo.conf": b"two"}, 2560, 1440)
        second = installer.read_manifest(self.game)
        self.assertEqual(first["files"]["dgVoodoo.conf"]["backup"], second["files"]["dgVoodoo.conf"]["backup"])
        installer.uninstall(self.game)
        self.assertEqual(self.path.read_bytes(), b"original")
        self.assertFalse((self.game / "D3D8.dll").exists())

    def test_restore_refuses_changed_files_then_preserves_them(self):
        installer.apply_files(self.game, {"dgVoodoo.conf": b"installed"}, 3440, 1440)
        self.path.write_bytes(b"later user settings")
        with self.assertRaisesRegex(ValueError, "changed since"):
            installer.uninstall(self.game)
        self.assertEqual(self.path.read_bytes(), b"later user settings")
        installer.uninstall(self.game, preserve_changed=True)
        self.assertEqual(self.path.read_bytes(), b"original")
        backups = list((self.game / installer.STATE / "backups").glob("before-restore-*/dgVoodoo.conf"))
        self.assertEqual(backups[0].read_bytes(), b"later user settings")

    def test_write_failure_rolls_back_files_and_manifest(self):
        write = installer.atomic_write

        def fail(path, data):
            if path == self.game / "D3D8.dll":
                raise OSError("simulated disk failure")
            write(path, data)

        with patch.object(installer, "atomic_write", side_effect=fail):
            with self.assertRaises(OSError):
                installer.apply_files(self.game, {"dgVoodoo.conf": b"new", "D3D8.dll": b"new"}, 3440, 1440)
        self.assertEqual(self.path.read_bytes(), b"original")
        self.assertFalse(installer.manifest_path(self.game).exists())

    def test_corrupt_backup_is_not_restored(self):
        installer.apply_files(self.game, {"dgVoodoo.conf": b"installed"}, 3440, 1440)
        backup = installer.read_manifest(self.game)["files"]["dgVoodoo.conf"]["backup"]
        (self.game / installer.STATE / backup).write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "checksum"):
            installer.uninstall(self.game)
        self.assertEqual(self.path.read_bytes(), b"installed")

    def test_manifest_cannot_restore_outside_game(self):
        installer.apply_files(self.game, {"dgVoodoo.conf": b"installed"}, 3440, 1440)
        manifest = installer.read_manifest(self.game)
        manifest["files"]["../outside.txt"] = manifest["files"]["dgVoodoo.conf"]
        installer.write_manifest(self.game, manifest)
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            installer.uninstall(self.game)

    def test_unsupported_game_is_rejected(self):
        (self.game / "RT3.exe").write_bytes(b"unsupported")
        with self.assertRaisesRegex(ValueError, "Unsupported RT3"):
            installer.check_game(self.game)

    def test_included_wrapper_is_exact_official_build(self):
        dll, config, cpl = installer.wrapper_files()
        self.assertEqual(installer.digest(dll), WRAPPER_SHA256)
        self.assertEqual(installer.digest(cpl), CPL_SHA256)
        self.assertIn(b"[DirectX]", config)
        with self.assertRaisesRegex(ValueError, "checksum"):
            installer.wrapper_files(b"bad download")

    def test_install_and_restore_complete_fixture_offline(self):
        exe = self.game / "RT3.exe"
        exe.write_bytes(b"synthetic executable fixture")
        baseline = {
            ENGINE: struct.pack("<III", 1051, 1600, 1200) + bytes(40),
            HOTKEYS: "\r\n".join(f"{name} = F12" for name in BINDINGS).encode(),
        }
        self.path.unlink()
        for name, data in baseline.items():
            target = self.game / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        with patch.object(installer, "EXE_SHA256", installer.digest(exe.read_bytes())), \
                patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected network access")):
            installer.install(self.game, 3440, 1440)
            self.assertEqual(installer.read_manifest(self.game)["status"], "installed")
            self.assertTrue((self.game / "Launch RT3 Ultrawide.cmd").exists())
            self.assertIn(b"dgVoodooWatermark", self.path.read_bytes())
            # Emulate RT3 persisting its runtime windowed flag on exit.
            engine = bytearray((self.game / ENGINE).read_bytes())
            engine[16] = 0
            (self.game / ENGINE).write_bytes(engine)
            installer.prepare_launch(self.game)
            self.assertEqual((self.game / ENGINE).read_bytes()[16], 1)
            installer.uninstall(self.game)
        for name, data in baseline.items():
            self.assertEqual((self.game / name).read_bytes(), data)
        self.assertFalse((self.game / "D3D8.dll").exists())
        self.assertFalse(self.path.exists())
        self.assertFalse((self.game / "dgVoodooCpl.exe").exists())

    def test_running_game_stops_install_before_changes(self):
        with patch.object(installer, "check_game", return_value=self.game), \
                patch.object(installer, "require_closed", side_effect=RuntimeError("Game is running")):
            with self.assertRaisesRegex(RuntimeError, "running"):
                installer.install(self.game, 3440, 1440)
        self.assertEqual(self.path.read_bytes(), b"original")
        self.assertFalse(installer.manifest_path(self.game).exists())

    def test_known_wrapper_upgrade_preserves_config_and_restores_old_binaries(self):
        baseline = {ENGINE: struct.pack("<III", 1051, 1600, 1200) + bytes(40),
                    HOTKEYS: "\n".join(f"{name} = F12" for name in BINDINGS).encode(),
                    "D3D8.dll": b"known older wrapper fixture",
                    "dgVoodooCpl.exe": b"known older control panel fixture",
                    "dgVoodoo.conf": b"[General]\nOutputAPI = bestavailable\n[DirectX]\nVRAM = 512\n"}
        for name, data in baseline.items():
            path = self.game / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        with patch.object(installer, "check_game", return_value=self.game), \
                patch.object(installer, "UPGRADE_WRAPPER_SHA256", installer.digest(baseline["D3D8.dll"])), \
                patch.object(installer, "UPGRADE_CPL_SHA256", installer.digest(baseline["dgVoodooCpl.exe"])):
            installer.install(self.game, 3440, 1440)
            self.assertEqual(installer.digest((self.game / "D3D8.dll").read_bytes()), WRAPPER_SHA256)
            self.assertEqual(installer.digest((self.game / "dgVoodooCpl.exe").read_bytes()), CPL_SHA256)
            self.assertIn(b"VRAM = 512", self.path.read_bytes())
            self.assertIn(b"OutputAPI = bestavailable", self.path.read_bytes())
            installer.uninstall(self.game)
        for name, data in baseline.items():
            self.assertEqual((self.game / name).read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
