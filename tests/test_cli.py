from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

from jquants_return_ranking import cli


class CliTests(unittest.TestCase):
    def test_no_args_opens_tui(self):
        with patch("jquants_return_ranking.tui.run_tui", return_value=0) as run_tui:
            code = cli.main([])

        self.assertEqual(code, 0)
        run_tui.assert_called_once_with()

    def test_help_works(self):
        out = io.StringIO()
        with self.assertRaises(SystemExit) as caught:
            with contextlib.redirect_stdout(out):
                cli.main(["--help"])

        self.assertEqual(caught.exception.code, 0)
        self.assertIn("jrr", out.getvalue())

    def test_help_does_not_open_tui(self):
        with patch("jquants_return_ranking.tui.run_tui") as run_tui:
            with self.assertRaises(SystemExit):
                cli.main(["--help"])

        run_tui.assert_not_called()

    def test_rank_invokes_collection_and_prints(self):
        fake_key = type("Key", (), {"api_key": "secret", "source": "prompt", "config_path": None})()
        fake_row = object()
        with patch.object(cli, "require_api_key", return_value=fake_key) as require_key:
            with patch.object(cli, "build_clients", return_value=("bars", "master")):
                with patch.object(cli, "collect_ranking", return_value=[fake_row]) as collect:
                    with patch.object(cli, "print_table") as print_table:
                        code = cli.main(["rank", "--date", "2026-05-01"])

        self.assertEqual(code, 0)
        require_key.assert_called_once_with(save=False)
        collect.assert_called_once()
        print_table.assert_called_once_with([fake_row])

    def test_main_sanitizes_errors(self):
        err = io.StringIO()
        with patch.object(cli, "cmd_config_show", side_effect=RuntimeError("api_key = secret-token")):
            with contextlib.redirect_stderr(err):
                code = cli.main(["config", "show"])

        self.assertEqual(code, 1)
        self.assertNotIn("secret-token", err.getvalue())
        self.assertIn("[REDACTED]", err.getvalue())


if __name__ == "__main__":
    unittest.main()
