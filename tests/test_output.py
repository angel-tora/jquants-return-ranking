from __future__ import annotations

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from jquants_return_ranking.output import CSV_COLUMNS, print_table, write_csv
from jquants_return_ranking.ranking import RankingRow


def row() -> RankingRow:
    return RankingRow(
        requested_date=date(2026, 5, 1),
        base_date=date(2026, 5, 1),
        comparison_date=date(2025, 4, 30),
        rank=1,
        code="1111",
        company_name="テスト",
        market="プライム",
        start_close=100.0,
        end_close=150.0,
        price_change=50.0,
        return_pct=50.0,
    )


class OutputTests(unittest.TestCase):
    def test_print_table_contains_japanese_columns(self):
        out = io.StringIO()
        with redirect_stdout(out):
            print_table([row()])

        text = out.getvalue()
        self.assertIn("順位", text)
        self.assertIn("1年前終値", text)
        self.assertIn("上昇率%", text)
        self.assertIn("テスト", text)

    def test_write_csv_emits_expected_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ranking.csv"
            write_csv([row()], path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)

        self.assertEqual(reader.fieldnames, CSV_COLUMNS)
        self.assertEqual(rows[0]["Code"], "1111")
        self.assertEqual(rows[0]["PriceChange"], "50.0")


if __name__ == "__main__":
    unittest.main()

