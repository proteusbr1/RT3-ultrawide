import json
from pathlib import Path
import tempfile
import unittest

from rt3_ultrawide.runtime import reserve_session


class SessionTests(unittest.TestCase):
    def test_same_process_cannot_be_attached_twice_but_reused_pid_can(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            token = {"pid": 42, "created": 100}
            reserve_session(path, token)
            with self.assertRaisesRegex(RuntimeError, "already used"):
                reserve_session(path, token)
            newer = {"pid": 42, "created": 101}
            reserve_session(path, newer)
            self.assertEqual(json.loads((path / "session.json").read_text()), newer)
