from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .jquants import JQuantsClient, fetch_daily_bars, fetch_master

DEFAULT_TOP_N = 50
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_MAX_SEARCH_DAYS = 31


@dataclass(frozen=True)
class RankingRow:
    requested_date: date
    base_date: date
    comparison_date: date
    rank: int
    code: str
    company_name: str
    market: str
    start_close: float
    end_close: float
    price_change: float
    return_pct: float


def resolve_previous_trading_day(
    client: JQuantsClient,
    target_date: date,
    max_search_days: int = DEFAULT_MAX_SEARCH_DAYS,
) -> tuple[date, list[dict]]:
    if max_search_days < 0:
        raise ValueError("max_search_days must be non-negative.")
    current = target_date
    for _ in range(max_search_days + 1):
        rows = fetch_daily_bars(client, current)
        if rows:
            return current, rows
        current -= timedelta(days=1)
    raise RuntimeError(f"No trading day found on or before {target_date.isoformat()} within {max_search_days} days.")


def build_adjc_map(rows: list[dict]) -> dict[str, float]:
    prices = {}
    for row in rows:
        code = str(row.get("Code", ""))
        adj_close = coerce_positive_float(row.get("AdjC"))
        if code and adj_close is not None:
            prices[code] = adj_close
    return prices


def build_master_map(rows: list[dict]) -> dict[str, dict]:
    return {str(row.get("Code", "")): row for row in rows if row.get("Code")}


def display_code(code: str) -> str:
    code = str(code)
    if len(code) == 5 and code.endswith("0"):
        return code[:-1]
    return code


def coerce_positive_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def compute_ranking_rows(
    requested_date: date,
    base_date: date,
    comparison_date: date,
    base_prices: dict[str, float],
    comparison_prices: dict[str, float],
    master_rows: list[dict],
    top_n: int = DEFAULT_TOP_N,
) -> list[RankingRow]:
    master_map = build_master_map(master_rows)
    rows = []
    for code in sorted(master_map):
        start_close = comparison_prices.get(code)
        end_close = base_prices.get(code)
        if start_close is None or end_close is None:
            continue
        price_change = end_close - start_close
        return_pct = (end_close / start_close - 1.0) * 100.0
        master = master_map[code]
        rows.append(
            {
                "code": code,
                "company_name": str(master.get("CoName", "")),
                "market": str(master.get("MktNm", "") or master.get("Mkt", "")),
                "start_close": start_close,
                "end_close": end_close,
                "price_change": price_change,
                "return_pct": return_pct,
            }
        )
    rows.sort(key=lambda row: (-row["return_pct"], row["code"]))
    return [
        RankingRow(
            requested_date=requested_date,
            base_date=base_date,
            comparison_date=comparison_date,
            rank=index,
            code=display_code(str(row["code"])),
            company_name=str(row["company_name"]),
            market=str(row["market"]),
            start_close=float(row["start_close"]),
            end_close=float(row["end_close"]),
            price_change=float(row["price_change"]),
            return_pct=float(row["return_pct"]),
        )
        for index, row in enumerate(rows[:top_n], start=1)
    ]


def collect_ranking(
    bars_client: JQuantsClient,
    master_client: JQuantsClient,
    requested_date: date,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    top_n: int = DEFAULT_TOP_N,
    max_search_days: int = DEFAULT_MAX_SEARCH_DAYS,
) -> list[RankingRow]:
    if lookback_days <= 0:
        raise ValueError("lookback_days must be positive.")
    if top_n <= 0:
        raise ValueError("top_n must be positive.")
    base_date, base_rows = resolve_previous_trading_day(bars_client, requested_date, max_search_days)
    comparison_target = base_date - timedelta(days=lookback_days)
    comparison_date, comparison_rows = resolve_previous_trading_day(bars_client, comparison_target, max_search_days)
    master_rows = fetch_master(master_client, base_date)
    return compute_ranking_rows(
        requested_date=requested_date,
        base_date=base_date,
        comparison_date=comparison_date,
        base_prices=build_adjc_map(base_rows),
        comparison_prices=build_adjc_map(comparison_rows),
        master_rows=master_rows,
        top_n=top_n,
    )

