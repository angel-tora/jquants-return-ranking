from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jquants_return_ranking.config import API_KEY_ENV, load_api_key, require_api_key, save_api_key


class ConfigTests(unittest.TestCase):
    def test_env_wins_over_saved_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            save_api_key("saved", path)
            with patch.dict(os.environ, {API_KEY_ENV: "env"}, clear=True):
                key = load_api_key(path)

        self.assertEqual(key.api_key, "env")
        self.assertEqual(key.source, "env")

    def test_require_api_key_prompts_without_saving_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            with patch.dict(os.environ, {}, clear=True):
                with patch("getpass.getpass", return_value="prompted"):
                    key = require_api_key(save=False, path=path)

            self.assertEqual(key.api_key, "prompted")
            self.assertEqual(key.source, "prompt")
            self.assertFalse(path.exists())

    def test_require_api_key_can_save_prompted_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            with patch.dict(os.environ, {}, clear=True):
                with patch("getpass.getpass", return_value="prompted"):
                    key = require_api_key(save=True, path=path)

            self.assertEqual(key.source, "prompt_saved")
            self.assertTrue(path.exists())

    def test_save_api_key_limits_file_and_directory_permissions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "config.toml"
            save_api_key("saved", path)

            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), stat.S_IRWXU)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), stat.S_IRUSR | stat.S_IWUSR)


if __name__ == "__main__":
    unittest.main()
