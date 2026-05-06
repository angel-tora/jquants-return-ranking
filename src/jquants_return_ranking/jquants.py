from __future__ import annotations

import json
import time
from datetime import date, timedelta
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .dates import today_jst

DAILY_BARS_URL = "https://api.jquants.com/v2/equities/bars/daily"
EQUITIES_MASTER_URL = "https://api.jquants.com/v2/equities/master"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RateLimiter:
    def __init__(
        self,
        min_interval_seconds: float,
        sleep_func: Callable[[float], None] = time.sleep,
        monotonic_func: Callable[[], float] = time.monotonic,
    ) -> None:
        self.min_interval_seconds = min_interval_seconds
        self.sleep_func = sleep_func
        self.monotonic_func = monotonic_func
        self._last_request_started_at: float | None = None

    def wait(self) -> None:
        if self._last_request_started_at is not None:
            elapsed = self.monotonic_func() - self._last_request_started_at
            wait_seconds = self.min_interval_seconds - elapsed
            if wait_seconds > 0:
                self.sleep_func(wait_seconds)
        self._last_request_started_at = self.monotonic_func()


class JQuantsClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        opener: Callable[..., object] | None = None,
        request_timeout_seconds: float = 30.0,
        rate_limiter: RateLimiter | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        max_retries: int = 4,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.opener = opener or urlopen
        self.request_timeout_seconds = request_timeout_seconds
        self.rate_limiter = rate_limiter
        self.sleep_func = sleep_func
        self.max_retries = max_retries

    def request_json(self, params: dict[str, str]) -> dict:
        attempt = 0
        while True:
            if self.rate_limiter is not None:
                self.rate_limiter.wait()
            request = Request(
                f"{self.base_url}?{urlencode(params)}",
                headers={
                    "x-api-key": self.api_key,
                    "Accept": "application/json",
                    "User-Agent": "jquants-return-ranking/0.1.0",
                },
            )
            try:
                with self._open_request(request) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    raw = response.read().decode(charset)
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise RuntimeError("Unexpected response shape from J-Quants API.")
                return payload
            except HTTPError as exc:
                if exc.code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    self.sleep_func(_backoff_seconds(exc, attempt))
                    attempt += 1
                    continue
                raise RuntimeError(f"J-Quants API request failed with HTTP {exc.code}: {_read_error_body(exc)}") from exc
            except URLError as exc:
                if attempt < self.max_retries:
                    self.sleep_func(max(1.0, 2**attempt))
                    attempt += 1
                    continue
                raise RuntimeError(f"J-Quants API request failed: {exc}") from exc

    def _open_request(self, request: Request):
        if self.opener is urlopen:
            return self.opener(request, timeout=self.request_timeout_seconds)
        return self.opener(request)


def build_clients(api_key: str, max_calls_per_minute: int = 60, request_timeout_seconds: float = 30.0) -> tuple[JQuantsClient, JQuantsClient]:
    if max_calls_per_minute <= 0:
        raise ValueError("max calls per minute must be positive.")
    limiter = RateLimiter(60.0 / float(max_calls_per_minute))
    return (
        JQuantsClient(api_key, DAILY_BARS_URL, request_timeout_seconds=request_timeout_seconds, rate_limiter=limiter),
        JQuantsClient(api_key, EQUITIES_MASTER_URL, request_timeout_seconds=request_timeout_seconds, rate_limiter=limiter),
    )


def validate_api_key(
    api_key: str,
    target_date: date | None = None,
    max_search_days: int = 31,
    request_timeout_seconds: float = 30.0,
) -> date:
    if not api_key.strip():
        raise ValueError("API key must not be empty.")
    if max_search_days < 0:
        raise ValueError("max_search_days must be non-negative.")
    target_date = target_date or (today_jst() - timedelta(weeks=12))
    master_client = JQuantsClient(
        api_key=api_key,
        base_url=EQUITIES_MASTER_URL,
        request_timeout_seconds=request_timeout_seconds,
    )
    last_error: Exception | None = None
    for offset in range(max_search_days + 1):
        checked_date = target_date - timedelta(days=offset)
        try:
            rows = fetch_master(master_client, checked_date)
            if rows:
                return checked_date
        except Exception as exc:
            last_error = exc
    if last_error is not None:
        raise RuntimeError(f"API key validation failed: {last_error}") from last_error
    raise RuntimeError("API key validation failed: no issue metadata returned.")


def fetch_daily_bars(client: JQuantsClient, target_date: date) -> list[dict]:
    return fetch_paginated_rows(client, target_date, ("daily_quotes", "bars", "data", "items", "results"))


def fetch_master(client: JQuantsClient, target_date: date) -> list[dict]:
    payload = client.request_json({"date": target_date.isoformat()})
    rows = extract_rows(payload, ("data",))
    if not rows:
        raise RuntimeError("J-Quants equities/master returned no issue metadata.")
    return rows


def fetch_paginated_rows(client: JQuantsClient, target_date: date, row_keys: Iterable[str]) -> list[dict]:
    all_rows: list[dict] = []
    pagination_key = None
    while True:
        params = {"date": target_date.isoformat()}
        if pagination_key:
            params["pagination_key"] = pagination_key
        payload = client.request_json(params)
        all_rows.extend(extract_rows(payload, row_keys))
        pagination_key = extract_pagination_key(payload)
        if not pagination_key:
            return all_rows


def extract_rows(payload: object, row_keys: Iterable[str]) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in row_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def extract_pagination_key(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("pagination_key", "paginationKey", "next_page_token", "nextPageToken"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _backoff_seconds(exc: HTTPError, attempt: int) -> float:
    retry_after = exc.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 1.0)
        except ValueError:
            pass
    if exc.code == 429:
        return 60.0
    return max(1.0, 2**attempt)


def _read_error_body(exc: HTTPError) -> str:
    try:
        raw = exc.read()
    except Exception:
        raw = b""
    if not raw:
        return exc.reason or "no response body"
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return raw.decode("utf-8", errors="replace").strip() or (exc.reason or "unknown error")
    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return json.dumps(payload, ensure_ascii=False)
