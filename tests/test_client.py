"""クライアント生成のテスト."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from share.client import get_client


def test_get_client_with_valid_token(tmp_path):
    """有効なトークンがある場合のテスト."""
    token_path = tmp_path / "token.json"
    token_data = {
        "app_key": "test_key",
        "refresh_token": "test_refresh",
        "account_id": "dbid:test",
    }
    token_path.write_text(json.dumps(token_data))

    mock_dbx = MagicMock()
    with patch("share.client.get_token_path", return_value=token_path):
        with patch("share.client.dropbox.Dropbox", return_value=mock_dbx) as mock_init:
            client = get_client()

    assert client is mock_dbx
    mock_init.assert_called_once_with(
        oauth2_refresh_token="test_refresh",
        app_key="test_key",
    )


def test_get_client_no_token():
    """トークンファイルが存在しない場合のテスト."""
    with patch("share.client.get_token_path", return_value=Path("/nonexistent/token.json")):
        client = get_client()

    assert client is None


def test_get_client_invalid_json(tmp_path):
    """無効な JSON の場合のテスト."""
    token_path = tmp_path / "token.json"
    token_path.write_text("invalid json")

    with patch("share.client.get_token_path", return_value=token_path):
        client = get_client()

    assert client is None


def test_get_client_missing_fields(tmp_path):
    """refresh_token や app_key が欠損している場合のテスト."""
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"app_key": "only_key"}))

    with patch("share.client.get_token_path", return_value=token_path):
        client = get_client()

    assert client is None
