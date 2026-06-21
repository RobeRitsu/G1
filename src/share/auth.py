"""Dropbox 認証コマンド."""

import argparse
import json
import webbrowser

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

from share.client import get_client
from share.config import (
    DEFAULT_SCOPES,
    DROPBOX_APP_KEY,
    get_data_dir,
    get_token_path,
)


def _save_token(data: dict) -> None:
    """トークンをファイルに保存（パーミッション 0o600）."""
    import os

    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    token_path = get_token_path()
    fd = os.open(str(token_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_token() -> dict | None:
    """保存されたトークンを読み込む."""
    token_path = get_token_path()
    if not token_path.exists():
        return None
    try:
        with token_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _delete_token() -> None:
    """保存されたトークンを削除."""
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()


def cmd_auth(args: argparse.Namespace) -> int:  # noqa: ARG001
    """PKCE フローで認証し refresh_token を保存."""
    auth_flow = DropboxOAuth2FlowNoRedirect(
        DROPBOX_APP_KEY,
        use_pkce=True,
        token_access_type="offline",
        scope=DEFAULT_SCOPES,
    )
    authorize_url = auth_flow.start()

    print("ブラウザで認証画面を開きます...")
    webbrowser.open(authorize_url)

    print("")
    print("ブラウザが開かない場合は、直接アクセスしてください:")
    print("  " + authorize_url)
    print("")
    print("1. 「許可」をクリックします")
    print("2. 表示された認証コードをコピーしてください")
    print("3. 以下に貼り付けてください")

    auth_code = input("認証コード: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print(f"エラー: 認証に失敗しました ― {e}")
        return 1

    token_data = {
        "app_key": DROPBOX_APP_KEY,
        "refresh_token": oauth_result.refresh_token,
        "account_id": getattr(oauth_result, "account_id", None),
    }
    _save_token(token_data)

    print("認証が完了しました。トークンを保存しました。")
    return 0


def cmd_auth_status(args: argparse.Namespace) -> int:  # noqa: ARG001
    """現在の認証状態を確認."""
    token_data = _load_token()
    if token_data is None:
        print("未認証です。'share auth' を実行してください。")
        return 1

    client = get_client()
    if client is None:
        print("トークンが破損しています。'share auth' で再認証してください。")
        return 1

    try:
        account = client.users_get_current_account()
        print(f"認証済み: {account.name.display_name} ({account.email})")
    except dropbox.exceptions.AuthError:
        print("トークンが無効です。'share auth' で再認証してください。")
        return 1
    except Exception as e:
        print(f"エラー: {e}")
        return 1

    return 0


def cmd_auth_logout(args: argparse.Namespace) -> int:  # noqa: ARG001
    """保存された認証情報を削除."""
    _delete_token()
    print("認証情報を削除しました。")
    return 0


def add_auth_parser(sub: argparse._SubParsersAction) -> None:
    """auth サブコマンドを登録."""
    parser = sub.add_parser("auth", help="Dropbox 認証を管理")
    parser.add_argument(
        "--status",
        action="store_true",
        help="認証状態を確認",
    )
    parser.add_argument(
        "--logout",
        action="store_true",
        help="認証情報を削除",
    )
    parser.set_defaults(func=cmd_auth_dispatch)


def cmd_auth_dispatch(args: argparse.Namespace) -> int:
    """--status / --logout の振り分け."""
    if args.logout:
        return cmd_auth_logout(args)
    if args.status:
        return cmd_auth_status(args)
    return cmd_auth(args)
