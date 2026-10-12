from pathlib import Path
import tempfile
import unittest

from rt3_ultrawide.controls import enabled, set_enabled


class ControlsTests(unittest.TestCase):
    def test_mouse_preference_persists_and_can_be_reenabled(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            self.assertTrue(enabled(game))
            set_enabled(game, False)
            self.assertFalse(enabled(game))
            set_enabled(game, True)
            self.assertTrue(enabled(game))
            set_enabled(game, True)

