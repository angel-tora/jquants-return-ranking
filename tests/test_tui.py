from __future__ import annotations

import unittest
from unittest.mock import patch

from jquants_return_ranking import tui


class TuiTests(unittest.TestCase):
    def test_run_tui_reports_missing_textual(self):
        with patch.dict("sys.modules", {"textual.app": None}):
            code = tui.run_tui()

        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()

