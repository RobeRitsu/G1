# share — Dropbox 共有リンク発行 CLI

Dropbox 上のファイルを選択して共有リンクを発行・管理する CLI ツール

## セットアップ（チーム共通）

[uv](https://docs.astral.sh/uv/) を使用

```bash
uv sync          # pyproject.toml / uv.lock 通りに環境を再現
```

## 使い方

### 基本コマンド

```bash
# Dropbox にログイン
uv run share auth

# コマンド一覧の確認
uv run share --help
```

### 品質チェック

```bash
uv run pytest              # テスト + カバレッジ
uv run flake8 src          # 静的解析
uv run radon cc src -a     # 複雑度チェック
```

インストールすると `share` コマンドとして直接実行できる

```bash
uv pip install -e .
share --help
```

## 構成

```
src/share/
├── __init__.py
├── auth.py       # 認証（ログイン・ログアウト）
├── cli.py        # コマンドの入り口
├── client.py     # Dropbox 接続
├── config.py     # 設定
└── upload.py     # ファイルアップロード

tests/           # ユニットテスト
```

## 担当機能（各自実装）

- 認証・main管理：Tani
- ローカルファイルのアップロード：Nakatani
- 共有リンクの発行：Daito
- 共有中ファイルの一覧表示：Nishio
- 共有の停止 / 削除：Ito