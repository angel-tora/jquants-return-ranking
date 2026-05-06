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

    def test_tui_source_mentions_date_buttons_and_default_date(self):
        with open(tui.__file__, encoding="utf-8") as handle:
            source = handle.read()

        self.assertIn("default_free_plan_date", source)
        self.assertIn("date-panel", source)
        self.assertIn('id="year"', source)
        self.assertIn('id="month"', source)
        self.assertIn('id="day"', source)
        self.assertIn("date-month-minus", source)
        self.assertIn("date-month-plus", source)
        self.assertIn("date-day-minus", source)
        self.assertIn("date-day-plus", source)


if __name__ == "__main__":
    unittest.main()
