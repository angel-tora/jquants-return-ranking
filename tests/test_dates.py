from __future__ import annotations

import unittest
from datetime import date

from jquants_return_ranking.dates import default_free_plan_date


class DatesTests(unittest.TestCase):
    def test_default_free_plan_date_is_twelve_weeks_before_today(self):
        self.assertEqual(default_free_plan_date(date(2026, 5, 6)), date(2026, 2, 11))


if __name__ == "__main__":
    unittest.main()
