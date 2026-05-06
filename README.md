# jquants-return-ranking

`jrr` は、J-Quants v2 の株価データを使って、日本株の過去1年の株価上昇率ランキング上位50件を表示するCLI/TUIツールです。

標準の出力項目は以下です。

- 順位
- コード
- 銘柄名
- 市場
- 1年前終値
- 指定日終値
- 上昇額
- 上昇率%

株価は調整後終値 `AdjC` を使って計算します。株式分割などの影響をある程度自然に扱うためです。

## インストール

必要なもの:

- Python 3.11以上
- J-Quants APIキー

GitHubからインストールする場合:

```bash
pipx install git+https://github.com/angel-tora/jquants-return-ranking.git
```

ローカル開発用:

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

`git clone` はソースコードを取得するだけです。`jrr` を実行する前に、`python -m pip install -e .` でパッケージをインストールしてください。

Windows cmd.exe:

```bat
git clone https://github.com/angel-tora/jquants-return-ranking.git
cd jquants-return-ranking
py -3.11 -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -e .
jrr
```

Windowsで `py -3.11` が使えない場合は、Python 3.11のフルパスを指定してください。

```bat
C:\Users\<UserName>\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv
```

仮想環境を有効化していない場合は、以下のように直接実行できます。

```powershell
.\.venv\Scripts\jrr.exe
```

## 使い方

```bash
jrr
```

引数なしで `jrr` を実行するとTUIが起動します。指定日とTop数を入力してランキングを取得します。
APIキーが設定されていない場合は、TUI上でAPIキーを入力して認証してください。
TUIで入力したAPIキーは現在のセッション内だけで使われ、保存されません。
日付欄の初期値は、J-Quantsの無料プランでも動きやすいように「今日から12週間前」です。

一度だけターミナルに出力する場合:

```bash
jrr rank --date 2026-05-01
```

APIキーが見つからない場合、`jrr` はターミナルでAPIキー入力を求めます。入力内容は表示されません。
明示的に保存を指定しない限り、APIキーは保存されません。

```bash
jrr rank --date 2026-05-01 --save-api-key
jrr config set-api-key
jrr config show
```

CSV保存が必要な場合:

```bash
jrr rank --date 2026-05-01 --output ranking.csv
```

## APIキー

APIキーは以下の順番で探します。

1. `JQUANTS_API_KEY`
2. 保存済みの設定ファイル
3. ターミナルでの非表示入力

保存済みの設定ファイルは、OS標準の設定ディレクトリ配下の `jquants-return-ranking` に置かれます。

セキュリティ上の注意:

- 実際のAPIキーをGitHub Issue、スクリーンショット、ログ、テストデータに貼らないでください。
- TUIで入力したAPIキーは保存されません。
- `jrr config set-api-key` と `jrr rank --save-api-key` は、意図的にローカル設定ファイルへAPIキーを保存します。保存したくない場合は `JQUANTS_API_KEY` を使ってください。
- OSが対応している場合、保存済み設定ファイルはユーザー本人だけが読める権限で作成します。

## 注意事項

- このツールはJ-Quants v2エンドポイントを使います。
- 市場データはユーザー自身のPC上で、ユーザー自身のAPIキーを使って取得します。
- このリポジトリには実データを同梱しません。
- このツールは投資助言ではありません。
