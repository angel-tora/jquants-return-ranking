from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from .config import load_api_key
from .dates import add_months_clamped, default_free_plan_date
from .jquants import build_clients, validate_api_key
from .output import write_csv
from .ranking import DEFAULT_LOOKBACK_DAYS, DEFAULT_MAX_SEARCH_DAYS, DEFAULT_TOP_N, RankingRow, collect_ranking


def run_tui() -> int:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Button, DataTable, Footer, Header, Input, Static
    except ImportError:
        print("Textual is not installed. Install with: pip install textual")
        return 1

    class ReturnRankingApp(App):
        CSS = """
        Screen { layout: vertical; }
        #intro { padding: 1 2; height: 7; }
        #api-key-panel { height: 5; padding: 1 2; }
        #controls { height: 13; padding: 1 2; }
        #date-panel { height: 8; border: round $primary; padding: 1 2; }
        #date-heading { height: 1; }
        #date-values { height: 3; }
        #date-buttons { height: 3; }
        #action-controls { height: 3; }
        #status { height: 2; padding: 0 2; }
        DataTable { height: 1fr; }
        #month, #day { width: 8; }
        #top { width: 18; }
        Button { width: 10; }
        .date-cell { width: 10; text-align: center; }
        """

        BINDINGS = [("q", "quit", "終了"), ("s", "save_csv", "CSV保存")]

        def __init__(self) -> None:
            super().__init__()
            self.rows: list[RankingRow] = []
            self.current_requested_date = ""
            self.api_key: str | None = None
            self.api_key_source = "missing"
            self.api_key_validated = False
            self.api_key_checked_date = None
            self.default_requested_date = default_free_plan_date()

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(id="intro"):
                yield Static("J-Quants 1年株価上昇ランキング", id="title")
                yield Static(
                    "指定日とTop数を入力して取得してください。価格は調整後終値 AdjC を使います。"
                )
                yield Static("", id="key-status")
            with Horizontal(id="api-key-panel"):
                yield Input(placeholder="J-Quants API key", password=True, id="api-key")
                yield Button("認証", id="validate-key", variant="success")
            with Vertical(id="controls"):
                with Vertical(id="date-panel"):
                    yield Static("指定日", id="date-title")
                    with Horizontal(id="date-heading"):
                        yield Static("年", classes="date-cell")
                        yield Static("月", classes="date-cell")
                        yield Static("日", classes="date-cell")
                    with Horizontal(id="date-values"):
                        yield Static(str(self.default_requested_date.year), id="year", classes="date-cell")
                        yield Input(value=f"{self.default_requested_date.month:02d}", placeholder="MM", id="month")
                        yield Input(value=f"{self.default_requested_date.day:02d}", placeholder="DD", id="day")
                    with Horizontal(id="date-buttons"):
                        yield Static("", classes="date-cell")
                        yield Button("月-", id="date-month-minus")
                        yield Button("月+", id="date-month-plus")
                        yield Button("日-", id="date-day-minus")
                        yield Button("日+", id="date-day-plus")
                with Horizontal(id="action-controls"):
                    yield Input(value=str(DEFAULT_TOP_N), placeholder="Top数", id="top")
                    yield Button("取得", id="fetch", variant="primary")
                    yield Button("CSV保存", id="save")
                    yield Button("終了", id="quit")
            yield Static("Ready", id="status")
            yield DataTable(id="table")
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one("#table", DataTable)
            table.add_columns("順位", "コード", "銘柄名", "市場", "1年前終値", "指定日終値", "上昇額", "上昇率%")
            self.load_initial_api_key()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "fetch":
                self.fetch()
            elif event.button.id == "save":
                self.save_csv()
            elif event.button.id == "quit":
                self.exit()
            elif event.button.id == "validate-key":
                self.validate_key_from_input()
            elif event.button.id == "date-month-minus":
                self.adjust_date(months=-1)
            elif event.button.id == "date-month-plus":
                self.adjust_date(months=1)
            elif event.button.id == "date-day-minus":
                self.adjust_date(days=-1)
            elif event.button.id == "date-day-plus":
                self.adjust_date(days=1)

        def action_save_csv(self) -> None:
            self.save_csv()

        def load_initial_api_key(self) -> None:
            key = load_api_key()
            if key.api_key:
                self.api_key = key.api_key
                self.api_key_source = key.source
                self.query_one("#api-key-panel").display = False
                self.set_key_status(f"APIキー: {key.source} / 未認証。取得前に認証します。")
                return
            self.set_key_status("APIキー: 未設定。入力して認証してください。保存はしません。")

        def set_status(self, message: str) -> None:
            self.query_one("#status", Static).update(message)

        def set_key_status(self, message: str) -> None:
            self.query_one("#key-status", Static).update(message)

        def adjust_date(self, months: int = 0, days: int = 0) -> None:
            try:
                current_date = self.current_selected_date()
            except Exception:
                self.set_selected_date(self.default_requested_date)
                self.set_status(f"日付が不正だったため初期値 {self.default_requested_date.isoformat()} に戻しました。")
                return
            if months:
                current_date = add_months_clamped(current_date, months)
            if days:
                current_date = current_date + timedelta(days=days)
            self.set_selected_date(current_date)

        def current_selected_date(self) -> date:
            year = int(str(self.query_one("#year", Static).renderable))
            month = int(self.query_one("#month", Input).value.strip())
            day = int(self.query_one("#day", Input).value.strip())
            return date(year, month, day)

        def set_selected_date(self, value: date) -> None:
            self.query_one("#year", Static).update(str(value.year))
            self.query_one("#month", Input).value = f"{value.month:02d}"
            self.query_one("#day", Input).value = f"{value.day:02d}"

        def validate_key_from_input(self) -> None:
            api_key = self.query_one("#api-key", Input).value.strip()
            if not api_key:
                self.set_key_status("APIキーを入力してください。")
                return
            self.validate_and_store_api_key(api_key, source="tui")

        def validate_and_store_api_key(self, api_key: str, source: str) -> bool:
            try:
                self.set_key_status("APIキー認証中...")
                checked_date = validate_api_key(api_key)
            except Exception as exc:
                self.api_key_validated = False
                self.set_key_status(f"APIキー認証エラー: {exc}")
                if source != "tui":
                    self.api_key = None
                    self.api_key_source = "missing"
                    self.query_one("#api-key-panel").display = True
                return False
            self.api_key = api_key
            self.api_key_source = source
            self.api_key_validated = True
            self.api_key_checked_date = checked_date
            self.query_one("#api-key", Input).value = ""
            self.query_one("#api-key-panel").display = False
            self.set_key_status(f"APIキー認証OK / 確認日 {checked_date.isoformat()}")
            return True

        def fetch(self) -> None:
            try:
                requested_date = self.current_selected_date()
                top_n = int(self.query_one("#top", Input).value.strip() or str(DEFAULT_TOP_N))
                if top_n <= 0:
                    raise ValueError("Top数は1以上にしてください。")
            except Exception as exc:
                self.set_status(f"入力エラー: {exc}")
                return

            try:
                if not self.api_key:
                    self.set_status("先にAPIキーを入力して認証してください。")
                    self.query_one("#api-key-panel").display = True
                    return
                if not self.api_key_validated and not self.validate_and_store_api_key(self.api_key, self.api_key_source):
                    self.set_status("APIキー認証に失敗しました。APIキーを入力し直してください。")
                    return
                self.set_status("取得中...")
                bars_client, master_client = build_clients(self.api_key)
                self.rows = collect_ranking(
                    bars_client=bars_client,
                    master_client=master_client,
                    requested_date=requested_date,
                    lookback_days=DEFAULT_LOOKBACK_DAYS,
                    top_n=top_n,
                    max_search_days=DEFAULT_MAX_SEARCH_DAYS,
                )
                self.current_requested_date = requested_date.isoformat()
                self.render_rows()
                if self.rows:
                    first = self.rows[0]
                    self.set_status(
                        f"{len(self.rows)}件 / 基準取引日 {first.base_date.isoformat()} / 比較取引日 {first.comparison_date.isoformat()}"
                    )
                else:
                    self.set_status("該当する銘柄がありません。")
            except Exception as exc:
                self.set_status(f"取得エラー: {exc}")

        def render_rows(self) -> None:
            table = self.query_one("#table", DataTable)
            table.clear()
            for row in self.rows:
                table.add_row(
                    str(row.rank),
                    row.code,
                    row.company_name,
                    row.market,
                    f"{row.start_close:,.1f}",
                    f"{row.end_close:,.1f}",
                    f"{row.price_change:,.1f}",
                    f"{row.return_pct:.2f}",
                )

        def save_csv(self) -> None:
            if not self.rows:
                self.set_status("保存するランキングがありません。先に取得してください。")
                return
            filename = f"ranking_{self.current_requested_date or self.rows[0].requested_date.isoformat()}.csv"
            path = Path.cwd() / filename
            try:
                write_csv(self.rows, path)
                self.set_status(f"CSV保存: {path}")
            except Exception as exc:
                self.set_status(f"保存エラー: {exc}")

    ReturnRankingApp().run()
    return 0
