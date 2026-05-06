# jquants-return-ranking

`jrr` shows the top 50 Japanese stocks by one-year price return using J-Quants v2 data.

The default output is a Japanese terminal table with:

- 順位
- コード
- 銘柄名
- 市場
- 1年前終値
- 指定日終値
- 上昇額
- 上昇率%

Prices are calculated with adjusted close (`AdjC`) so stock splits are handled more naturally.

## Install

Requirements:

- Python 3.11 or newer
- A J-Quants API key

From GitHub:

```bash
pipx install git+https://github.com/angel-tora/jquants-return-ranking.git
```

Local development:

```bash
git clone https://github.com/angel-tora/jquants-return-ranking.git
cd jquants-return-ranking
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
git clone https://github.com/angel-tora/jquants-return-ranking.git
cd jquants-return-ranking
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
jrr
```

`git clone` only downloads the source code. Install the package with `python -m pip install -e .` before running `jrr`.

Windows cmd.exe:

```bat
git clone https://github.com/angel-tora/jquants-return-ranking.git
cd jquants-return-ranking
py -3.11 -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -e .
jrr
```

If `py -3.11` is not available on Windows, use the full Python 3.11 path:

```bat
C:\Users\<UserName>\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv
```

If the virtual environment is not activated, run the command by path:

```powershell
.\.venv\Scripts\jrr.exe
```

## Usage

```bash
jrr
```

`jrr` opens the TUI. Enter a date and Top count, then fetch the ranking.
If no API key is configured, enter it in the TUI and authenticate it first.
The TUI uses the key only for the current session and does not save it.
The date field starts at 12 weeks before today for free-plan compatibility.

For one-shot terminal output:

```bash
jrr rank --date 2026-05-01
```

If an API key is not found, `jrr` asks for it in the terminal without echoing.
The key is not saved unless you explicitly request it.

```bash
jrr rank --date 2026-05-01 --save-api-key
jrr config set-api-key
jrr config show
```

Save CSV only when needed:

```bash
jrr rank --date 2026-05-01 --output ranking.csv
```

## API Key

Lookup order:

1. `JQUANTS_API_KEY`
2. saved config file
3. hidden terminal prompt

The saved config file lives in the OS-standard config directory for
`jquants-return-ranking`.

Security notes:

- Do not paste real API keys into GitHub issues, screenshots, logs, or test fixtures.
- TUI key input is session-only and is not written to disk.
- `jrr config set-api-key` and `jrr rank --save-api-key` intentionally write a local config file. Use `JQUANTS_API_KEY` instead if you do not want a saved file.
- Saved config files are written with user-only permissions where the OS supports it.

## Notes

- This tool uses J-Quants v2 endpoints.
- Market data is fetched on the user's machine with the user's own API key.
- No real market data is bundled in this repository.
- This is not investment advice.
