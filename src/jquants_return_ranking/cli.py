from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import API_KEY_ENV, load_api_key, prompt_and_save_api_key, require_api_key
from .dates import parse_date, today_jst
from .jquants import build_clients
from .output import print_table, write_csv
from .ranking import DEFAULT_LOOKBACK_DAYS, DEFAULT_MAX_SEARCH_DAYS, DEFAULT_TOP_N, collect_ranking


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jrr", description="J-Quants 1年株価上昇ランキングCLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rank = subparsers.add_parser("rank", help="指定日から過去1年の上昇率ランキングを表示します。")
    rank.add_argument("--date", type=parse_date, default=today_jst(), help="指定日 YYYY-MM-DD。省略時はJSTの今日。")
    rank.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    rank.add_argument("--top", type=int, default=DEFAULT_TOP_N)
    rank.add_argument("--max-search-days", type=int, default=DEFAULT_MAX_SEARCH_DAYS)
    rank.add_argument("--max-calls-per-minute", type=int, default=60)
    rank.add_argument("--request-timeout-seconds", type=float, default=30.0)
    rank.add_argument("--output", type=Path, help="指定した場合のみCSV保存します。")
    rank.add_argument("--save-api-key", action="store_true", help="プロンプト入力したAPIキーを保存します。")
    rank.set_defaults(func=cmd_rank)

    config = subparsers.add_parser("config", help="APIキー設定を管理します。")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    set_key = config_sub.add_parser("set-api-key", help="APIキーを保存します。")
    set_key.set_defaults(func=cmd_config_set_api_key)
    show = config_sub.add_parser("show", help="設定状態を表示します。APIキー本体は表示しません。")
    show.set_defaults(func=cmd_config_show)

    return parser


def cmd_rank(args: argparse.Namespace) -> int:
    if args.lookback_days <= 0:
        raise ValueError("--lookback-days must be positive.")
    if args.top <= 0:
        raise ValueError("--top must be positive.")
    if args.max_search_days < 0:
        raise ValueError("--max-search-days must be non-negative.")
    if args.max_calls_per_minute <= 0:
        raise ValueError("--max-calls-per-minute must be positive.")
    if args.request_timeout_seconds <= 0:
        raise ValueError("--request-timeout-seconds must be positive.")

    key = require_api_key(save=args.save_api_key)
    bars_client, master_client = build_clients(
        key.api_key or "",
        max_calls_per_minute=args.max_calls_per_minute,
        request_timeout_seconds=args.request_timeout_seconds,
    )
    rows = collect_ranking(
        bars_client=bars_client,
        master_client=master_client,
        requested_date=args.date,
        lookback_days=args.lookback_days,
        top_n=args.top,
        max_search_days=args.max_search_days,
    )
    print_table(rows)
    if args.output:
        write_csv(rows, args.output)
        print(f"CSV保存: {args.output}")
    return 0


def cmd_config_set_api_key(args: argparse.Namespace) -> int:
    path = prompt_and_save_api_key()
    print(f"APIキーを保存しました: {path}")
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    key = load_api_key()
    print(f"config_path={key.config_path}")
    print(f"api_key_set={key.api_key is not None}")
    print(f"api_key_source={key.source}")
    print(f"env_name={API_KEY_ENV}")
    return 0

