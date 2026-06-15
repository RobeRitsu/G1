# share — Dropbox 共有リンク発行 CLI

Dropbox 上のファイルを選択して共有リンクを発行・管理する CLI ツール

## セットアップ（チーム共通）

[uv](https://docs.astral.sh/uv/) を使用

```bash
uv sync          # pyproject.toml / uv.lock 通りに環境を再現
```

## 使い方

```bash
uv run share --help        # コマンドの確認
uv run pytest              # ユニットテスト + カバレッジ
uv run radon cc src -a     # 循環的複雑度
uv run flake8 src          # 静的解析
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
└── cli.py       # コマンドのエントリポイント（サブコマンドは担当者が実装）
tests/           # ユニットテスト
```

## 担当機能（各自実装）

- 認証・main管理：Tani
- ローカルファイルのアップロード：Nakatani
- 共有リンクの発行：Daito
- 共有中ファイルの一覧表示：Nishio
- 共有の停止 / 削除：Ito