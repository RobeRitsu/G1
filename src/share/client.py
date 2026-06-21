"""Dropbox クライアント生成 — 他機能担当者向け IF."""

import json

import dropbox

from share.config import get_token_path


def get_client() -> dropbox.Dropbox | None:
    """保存された認証情報から Dropbox クライアントを生成.

    Returns:
        Dropbox: refresh_token から生成したクライアント.
        None: トークンが保存されていない場合.
    """
    token_path = get_token_path()
    if not token_path.exists():
        return None

    try:
        with token_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    refresh_token = data.get("refresh_token")
    app_key = data.get("app_key")
    if not refresh_token or not app_key:
        return None

    return dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
    )
