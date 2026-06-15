# Dropbox ファイル共有リンク発行 CLI ツール

## 概要

CUI（コマンドライン）上から Dropbox 上のファイルを選択し、共有リンクを発行できるツール。
コマンドとして登録し、ファイルの共有・一覧・共有停止を行える。

## 機能要件

| # | 機能 | 説明 |
|---|------|------|
| 1 | コマンドとしての登録 | OS のコマンドとして実行できるようにインストール／登録する |
| 2 | Dropbox との連携・認証 | Dropbox API での OAuth 認証・アクセストークン管理 |
| 3 | 共有リンクの発行 | ファイルを選択し、共有リンクを発行する |
| 4 | 共有ファイルの一覧表示 | 現在共有しているファイルを一覧表示する |
| 5 | 共有の削除（停止） | 共有中のファイルの共有を停止する |

## 授業で盛り込む内容（学習目的）

- **ユニットテスト** — `unittest` / `pytest` ＋ `unittest.mock`（`MagicMock`）で
  Dropbox SDK の呼び出しをモック化してテストする
- **品質メトリクスの計測** — カバレッジ・複雑度・静的解析などを計測する

## 技術スタック

| 区分 | 採用技術 |
|------|----------|
| 言語 | Python |
| 外部 API | Dropbox SDK（公式 Python SDK `dropbox`） |
| テスト | `unittest` / `pytest`、`unittest.mock`（`MagicMock`） |
| 品質メトリクス | `coverage.py`、`radon`、`flake8` / `pylint` など |
| バージョン管理 | GitHub |

## 参考リンク

- Dropbox Python SDK ドキュメント: https://www.dropbox.com/developers/documentation/python
- リポジトリ: https://github.com/tetra0717/G1

## コマンド設計（案）

```
share auth                 # Dropbox 認証を行う
share create <ファイルパス>  # 共有リンクを発行する
share list                 # 共有中ファイルを一覧表示する
share remove <ファイルパス>  # 共有を停止する
```

## 品質メトリクスの計測項目（案）

- テストカバレッジ（`coverage.py` / `pytest-cov`）
- 循環的複雑度・保守性指標（`radon`）
- コーディング規約・静的解析（`flake8` / `pylint`）
