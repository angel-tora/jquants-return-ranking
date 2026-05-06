from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from jquants_return_ranking import ranking


class FakeClient:
    def __init__(self, rows_by_date: dict[str, list[dict]]):
        self.rows_by_date = rows_by_date
        self.calls = []


def bars(date_value: str, code: str, adjc: object) -> dict:
    return {"Date": date_value, "Code": code, "AdjC": adjc}


class RankingTests(unittest.TestCase):
    def test_resolve_previous_trading_day_walks_back(self):
        client = FakeClient(
            {
                "2026-05-03": [],
                "2026-05-02": [],
                "2026-05-01": [bars("2026-05-01", "11110", 100)],
            }
        )

        with patch.object(ranking, "fetch_daily_bars", side_effect=lambda c, d: c.rows_by_date.get(d.isoformat(), [])):
            trading_day, rows = ranking.resolve_previous_trading_day(client, date(2026, 5, 3), max_search_days=3)

        self.assertEqual(trading_day, date(2026, 5, 1))
        self.assertEqual(rows[0]["Code"], "11110")

    def test_compute_ranking_rows_uses_adjc_and_master(self):
        rows = ranking.compute_ranking_rows(
            requested_date=date(2026, 5, 1),
            base_date=date(2026, 5, 1),
            comparison_date=date(2025, 5, 1),
            base_prices={"11110": 150.0, "22220": 220.0, "33330": 10.0},
            comparison_prices={"11110": 100.0, "22220": 200.0},
            master_rows=[
                {"Code": "11110", "CoName": "Alpha", "MktNm": "プライム"},
                {"Code": "22220", "CoName": "Beta", "MktNm": "グロース"},
                {"Code": "33330", "CoName": "Gamma", "MktNm": "スタンダード"},
            ],
            top_n=50,
        )

        self.assertEqual([row.code for row in rows], ["11110", "22220"])
        self.assertEqual(rows[0].company_name, "Alpha")
        self.assertEqual(rows[0].market, "プライム")
        self.assertAlmostEqual(rows[0].price_change, 50.0)
        self.assertAlmostEqual(rows[0].return_pct, 50.0)
        self.assertAlmostEqual(rows[1].return_pct, 10.0)

    def test_compute_ranking_rows_tie_breaks_by_code_and_limits_top_n(self):
        rows = ranking.compute_ranking_rows(
            requested_date=date(2026, 5, 1),
            base_date=date(2026, 5, 1),
            comparison_date=date(2025, 5, 1),
            base_prices={"22220": 120.0, "11110": 120.0, "33330": 130.0},
            comparison_prices={"22220": 100.0, "11110": 100.0, "33330": 100.0},
            master_rows=[
                {"Code": "22220", "CoName": "B", "MktNm": "P"},
                {"Code": "11110", "CoName": "A", "MktNm": "P"},
                {"Code": "33330", "CoName": "C", "MktNm": "P"},
            ],
            top_n=2,
        )

        self.assertEqual([row.code for row in rows], ["33330", "11110"])
        self.assertEqual([row.rank for row in rows], [1, 2])

    def test_build_adjc_map_skips_missing_and_non_positive(self):
        prices = ranking.build_adjc_map(
            [
                {"Code": "11110", "AdjC": "100"},
                {"Code": "22220", "AdjC": ""},
                {"Code": "33330", "AdjC": "0"},
                {"Code": "44440", "AdjC": "-1"},
            ]
        )

        self.assertEqual(prices, {"11110": 100.0})

    def test_collect_ranking_resolves_comparison_day(self):
        client = FakeClient({})
        master_client = FakeClient({})

        def fake_resolve(c, target_date, max_search_days):
            if target_date == date(2026, 5, 1):
                return date(2026, 5, 1), [bars("2026-05-01", "11110", 150)]
            self.assertEqual(target_date, date(2025, 5, 1))
            return date(2025, 4, 30), [bars("2025-04-30", "11110", 100)]

        with patch.object(ranking, "resolve_previous_trading_day", side_effect=fake_resolve):
            with patch.object(ranking, "fetch_master", return_value=[{"Code": "11110", "CoName": "Alpha", "MktNm": "プライム"}]):
                rows = ranking.collect_ranking(client, master_client, date(2026, 5, 1), lookback_days=365)

        self.assertEqual(rows[0].base_date, date(2026, 5, 1))
        self.assertEqual(rows[0].comparison_date, date(2025, 4, 30))


if __name__ == "__main__":
    unittest.main()

