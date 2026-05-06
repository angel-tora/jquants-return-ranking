from __future__ import annotations

import unittest
from datetime import date

from jquants_return_ranking.dates import add_months_clamped, default_free_plan_date


class DatesTests(unittest.TestCase):
    def test_default_free_plan_date_is_twelve_weeks_before_today(self):
        self.assertEqual(default_free_plan_date(date(2026, 5, 6)), date(2026, 2, 11))

    def test_add_months_clamped_handles_short_month(self):
        self.assertEqual(add_months_clamped(date(2026, 3, 31), -1), date(2026, 2, 28))

    def test_add_months_clamped_handles_leap_year(self):
        self.assertEqual(add_months_clamped(date(2024, 1, 31), 1), date(2024, 2, 29))


if __name__ == "__main__":
    unittest.main()
