# 開発者ガイド

各機能を実装する担当者向けのガイド

## 1. 前提

### 1.1 認証

`share auth` で Dropbox にログインすると、自動的にトークンが保存されます。
他のコマンドでは `get_client()` を使って接続します。

```python
from share.client import get_client

client = get_client()
if client is None:
    print("エラー: ログインが必要です")
    print("'share auth' を実行してください")
    return 1
```

### 1.2 ファイル構成

```
src/share/
├── cli.py        # コマンドの入り口（編集しない）
├── config.py     # 設定（編集しない）
├── client.py     # Dropbox 接続（編集しない）
├── auth.py       # 認証
└── upload.py     # ファイルアップロード
```

自分の担当ファイル以外は編集しないでください。

---

## 2. コマンドの作り方

### 2.1 必要な関数

`src/share/<機能名>.py` を作り、以下の2つの関数を実装してください。

```python
def cmd_xxx(args) -> int:
    """コマンド本体. 0=成功, 1=失敗"""
    ...

def add_xxx_parser(sub) -> None:
    """コマンドを登録する関数"""
    parser = sub.add_parser("xxx", help="説明")
    parser.add_argument("path", help="ファイルパス")
    parser.set_defaults(func=cmd_xxx)
```

### 2.2 登録

`cli.py` に `add_xxx_parser(sub)` を追加します。
実装が終わったら Tani に連絡してください。

### 2.3 作例（upload.py）

```python
def upload_file(dbx, local_path: str, dropbox_path: str | None = None):
    """コア処理. dbx は Dropbox クライアント"""
    with open(local_path, "rb") as f:
        return dbx.files_upload(f.read(), dropbox_path)

def cmd_upload(args) -> int:
    """コマンド本体"""
    from share.client import get_client
    
    dbx = get_client()
    if dbx is None:
        print("エラー: ログインが必要です")
        return 1
    
    metadata = upload_file(dbx, args.local_path, args.dropbox_path)
    print(f"完了: {metadata.path_display}")
    return 0

def add_upload_parser(sub) -> None:
    """コマンド登録"""
    parser = sub.add_parser("upload", help="ファイルをアップロード")
    parser.add_argument("local_path", help="アップロードするファイル")
    parser.set_defaults(func=cmd_upload)
```

---

## 3. エラー処理

```python
import dropbox.exceptions

try:
    result = client.sharing_create_shared_link_with_settings(args.path)
except dropbox.exceptions.ApiError as e:
    print(f"エラー: {e}")
    return 1
```

---

## 4. テストの書き方

### 4.1 ファイル名

`tests/test_<機能名>.py`

### 4.2 テスト方法

Dropbox に実際に接続せず、mock を使います。

```python
from unittest.mock import MagicMock
from share.upload import upload_file

def test_upload_file(tmp_path):
    dbx = MagicMock()
    dbx.files_upload.return_value = MagicMock(path_display="/test.txt")
    
    local = tmp_path / "test.txt"
    local.write_text("hello")
    
    result = upload_file(dbx, str(local))
    assert result.path_display == "/test.txt"
```

### 4.3 テストパターン

| ケース | 方法 |
|--------|------|
| 成功 | mock で正常値を返す |
| API エラー | `dbx.xx.side_effect = ApiError(...)` |
| 未ログイン | `patch("share.xxx.get_client", return_value=None)` |

---

## 5. チェック項目

実装後、以下を確認してください：

- [ ] `src/share/<機能名>.py` を作成
- [ ] `cmd_xxx()` と `add_xxx_parser()` を実装
- [ ] `get_client()` で認証チェック
- [ ] エラー処理を追加
- [ ] `tests/test_<機能名>.py` を作成
- [ ] 成功・失敗・未ログインのテストを書く
- [ ] `flake8` でチェック
- [ ] `pytest` で全テストが通る

---

## 6. よくある問題

**Q: `ModuleNotFoundError: No module named 'share'`**
A: `uv sync` を実行してください

**Q: `get_client()` が None を返す**
A: `share auth` でログインしてください

**Q: Dropbox の API 使い方が分からない**
A: [Dropbox Python SDK ドキュメント](http://dropbox-sdk-python.readthedocs.org/) を参照
