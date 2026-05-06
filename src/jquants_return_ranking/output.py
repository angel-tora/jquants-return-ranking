from __future__ import annotations

import csv
from pathlib import Path

from .ranking import RankingRow

CSV_COLUMNS = [
    "RequestedDate",
    "BaseDate",
    "ComparisonDate",
    "Rank",
    "Code",
    "CompanyName",
    "Market",
    "StartClose",
    "EndClose",
    "PriceChange",
    "ReturnPct",
]


def print_table(rows: list[RankingRow]) -> None:
    if not rows:
        print("該当する銘柄がありません。")
        return
    first = rows[0]
    print(
        f"指定日: {first.requested_date.isoformat()} / "
        f"基準取引日: {first.base_date.isoformat()} / "
        f"比較取引日: {first.comparison_date.isoformat()} / "
        f"Top{len(rows)}"
    )
    headers = ["順位", "コード", "銘柄名", "市場", "1年前終値", "指定日終値", "上昇額", "上昇率%"]
    body = [
        [
            str(row.rank),
            row.code,
            row.company_name,
            row.market,
            format_yen(row.start_close),
            format_yen(row.end_close),
            format_yen(row.price_change),
            f"{row.return_pct:.2f}",
        ]
        for row in rows
    ]
    widths = [display_width(value) for value in headers]
    for cells in body:
        widths = [max(width, display_width(cell)) for width, cell in zip(widths, cells)]
    print(format_row(headers, widths))
    print(" ".join("-" * width for width in widths))
    for cells in body:
        print(format_row(cells, widths))


def write_csv(rows: list[RankingRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_csv(row))


def row_to_csv(row: RankingRow) -> dict:
    return {
        "RequestedDate": row.requested_date.isoformat(),
        "BaseDate": row.base_date.isoformat(),
        "ComparisonDate": row.comparison_date.isoformat(),
        "Rank": row.rank,
        "Code": row.code,
        "CompanyName": row.company_name,
        "Market": row.market,
        "StartClose": row.start_close,
        "EndClose": row.end_close,
        "PriceChange": row.price_change,
        "ReturnPct": row.return_pct,
    }


def format_yen(value: float) -> str:
    return f"{value:,.1f}"


def format_row(cells: list[str], widths: list[int]) -> str:
    return " ".join(pad_display(cell, width) for cell, width in zip(cells, widths))


def pad_display(value: str, width: int) -> str:
    return value + " " * max(0, width - display_width(value))


def display_width(value: str) -> int:
    width = 0
    for char in value:
        width += 2 if ord(char) > 0xFF else 1
    return width

