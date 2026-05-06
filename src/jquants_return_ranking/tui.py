from __future__ import annotations

from pathlib import Path

from .config import load_api_key, require_api_key
from .dates import parse_date
from .jquants import build_clients
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
        #controls { height: 5; padding: 1 2; }
        #status { height: 2; padding: 0 2; }
        DataTable { height: 1fr; }
        Input { width: 24; }
        Button { width: 14; }
        """

        BINDINGS = [("q", "quit", "終了"), ("s", "save_csv", "CSV保存")]

        def __init__(self) -> None:
            super().__init__()
            self.rows: list[RankingRow] = []
            self.current_requested_date = ""

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(id="intro"):
                yield Static("J-Quants 1年株価上昇ランキング", id="title")
                yield Static(
                    "指定日とTop数を入力して取得してください。価格は調整後終値 AdjC を使います。"
                )
                yield Static(self.initial_key_status())
            with Horizontal(id="controls"):
                yield Input(placeholder="YYYY-MM-DD", id="date")
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

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "fetch":
                self.fetch()
            elif event.button.id == "save":
                self.save_csv()
            elif event.button.id == "quit":
                self.exit()

        def action_save_csv(self) -> None:
            self.save_csv()

        def initial_key_status(self) -> str:
            key = load_api_key()
            if key.api_key:
                return f"APIキー: {key.source}"
            return "APIキー: 未設定。取得時に非表示入力で求めます。保存する場合は jrr config set-api-key を使ってください。"

        def set_status(self, message: str) -> None:
            self.query_one("#status", Static).update(message)

        def fetch(self) -> None:
            try:
                requested_date_text = self.query_one("#date", Input).value.strip()
                if not requested_date_text:
                    raise ValueError("指定日を YYYY-MM-DD で入力してください。")
                requested_date = parse_date(requested_date_text)
                top_n = int(self.query_one("#top", Input).value.strip() or str(DEFAULT_TOP_N))
                if top_n <= 0:
                    raise ValueError("Top数は1以上にしてください。")
            except Exception as exc:
                self.set_status(f"入力エラー: {exc}")
                return

            try:
                self.set_status("取得中...")
                key = require_api_key(save=False)
                bars_client, master_client = build_clients(key.api_key or "")
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

