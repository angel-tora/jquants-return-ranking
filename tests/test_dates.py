from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from jquants_return_ranking import dates
from jquants_return_ranking.dates import default_free_plan_date


class DatesTests(unittest.TestCase):
    def test_default_free_plan_date_is_twelve_weeks_before_today(self):
        self.assertEqual(default_free_plan_date(date(2026, 5, 6)), date(2026, 2, 11))

    def test_today_jst_falls_back_when_zoneinfo_data_is_missing(self):
        class MissingZoneInfo:
            def __init__(self, key: str) -> None:
                raise dates.ZoneInfoNotFoundError(key)

        with patch.object(dates, "ZoneInfo", MissingZoneInfo):
            self.assertIsInstance(dates.today_jst(), date)


if __name__ == "__main__":
    unittest.main()
