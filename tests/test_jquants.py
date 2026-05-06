from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from jquants_return_ranking import jquants


class JQuantsTests(unittest.TestCase):
    def test_validate_api_key_returns_checked_date(self):
        with patch.object(jquants, "fetch_master", return_value=[{"Code": "11110"}]) as fetch_master:
            checked_date = jquants.validate_api_key("secret", target_date=date(2026, 1, 10))

        self.assertEqual(checked_date, date(2026, 1, 10))
        self.assertEqual(fetch_master.call_count, 1)

    def test_validate_api_key_walks_back_when_master_fails(self):
        calls = []

        def fake_fetch_master(client, target_date):
            calls.append(target_date)
            if target_date == date(2026, 1, 9):
                return [{"Code": "11110"}]
            raise RuntimeError("no rows")

        with patch.object(jquants, "fetch_master", side_effect=fake_fetch_master):
            checked_date = jquants.validate_api_key("secret", target_date=date(2026, 1, 10), max_search_days=2)

        self.assertEqual(checked_date, date(2026, 1, 9))
        self.assertEqual(calls, [date(2026, 1, 10), date(2026, 1, 9)])

    def test_validate_api_key_rejects_empty_key(self):
        with self.assertRaises(ValueError):
            jquants.validate_api_key("")


if __name__ == "__main__":
    unittest.main()
