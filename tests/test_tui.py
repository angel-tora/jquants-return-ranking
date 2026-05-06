from __future__ import annotations

import unittest
from unittest.mock import patch

from jquants_return_ranking import tui


class TuiTests(unittest.TestCase):
    def test_run_tui_reports_missing_textual(self):
        with patch.dict("sys.modules", {"textual.app": None}):
            code = tui.run_tui()

        self.assertEqual(code, 1)

    def test_tui_source_mentions_api_key_authentication(self):
        with open(tui.__file__, encoding="utf-8") as handle:
            source = handle.read()

        self.assertIn("APIキー認証OK", source)
        self.assertIn("api-key-panel", source)
        self.assertIn("validate-key", source)

    def test_tui_source_uses_default_date_without_date_buttons(self):
        with open(tui.__file__, encoding="utf-8") as handle:
            source = handle.read()

        self.assertIn("default_free_plan_date", source)
        self.assertNotIn("date-month-minus", source)
        self.assertNotIn("date-day-minus", source)


if __name__ == "__main__":
    unittest.main()
