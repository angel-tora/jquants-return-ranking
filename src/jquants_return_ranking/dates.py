from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


def today_jst() -> date:
    if ZoneInfo is not None:
        return datetime.now(tz=ZoneInfo("Asia/Tokyo")).date()
    return datetime.now(tz=timezone(timedelta(hours=9))).date()


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format.") from exc


def default_free_plan_date(today: date | None = None) -> date:
    return (today or today_jst()) - timedelta(weeks=12)


def add_months_clamped(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)
