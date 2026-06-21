"""認証コマンドのテスト."""

import argparse
import json
from unittest.mock import MagicMock, patch

import dropbox
from share import auth


def test_cmd_auth_success(monkeypatch):
    """正常な認証フローテスト."""
    mock_flow = MagicMock()
    mock_oauth_result = MagicMock()
    mock_oauth_result.refresh_token = "test_refresh_123"
    mock_oauth_result.account_id = "dbid:test123"
    mock_flow.start.return_value = "https://dropbox.com/oauth/authorize?test=1"
    mock_flow.finish.return_value = mock_oauth_result

    mock_save_called = {}

    def mock_save(data):
        mock_save_called["data"] = data

    with patch("share.auth.DropboxOAuth2FlowNoRedirect", return_value=mock_flow):
        with patch("share.auth._save_token", side_effect=mock_save):
            with patch("share.auth.webbrowser.open"):
                with patch("builtins.input", return_value="test_auth_code"):
                    args = argparse.Namespace(status=False, logout=False)
                    result = auth.cmd_auth(args)

    assert result == 0
    assert mock_save_called["data"]["refresh_token"] == "test_refresh_123"
    assert mock_save_called["data"]["app_key"] == auth.DROPBOX_APP_KEY


def test_cmd_auth_flow_error(monkeypatch):
    """認証フロー失敗時のテスト."""
    mock_flow = MagicMock()
    mock_flow.start.return_value = "https://dropbox.com/oauth/authorize"
    mock_flow.finish.side_effect = Exception("Invalid code")

    with patch("share.auth.DropboxOAuth2FlowNoRedirect", return_value=mock_flow):
        with patch("builtins.input", return_value="bad_code"):
            args = argparse.Namespace(status=False, logout=False)
            result = auth.cmd_auth(args)

    assert result == 1


def test_cmd_auth_status_authenticated(tmp_token_file, monkeypatch):
    """認証済み状態確認テスト."""
    mock_account = MagicMock()
    mock_account.name.display_name = "Test User"
    mock_account.email = "test@example.com"

    mock_client = MagicMock()
    mock_client.users_get_current_account.return_value = mock_account

    with patch("share.auth.get_client", return_value=mock_client):
        with patch("share.auth._load_token", return_value={
            "app_key": "test_key",
            "refresh_token": "test_refresh",
        }):
            args = argparse.Namespace()
            result = auth.cmd_auth_status(args)

    assert result == 0


def test_cmd_auth_status_not_authenticated():
    """未認証状態確認テスト."""
    with patch("share.auth._load_token", return_value=None):
        args = argparse.Namespace()
        result = auth.cmd_auth_status(args)

    assert result == 1


def test_cmd_auth_logout(tmp_path):
    """ログアウトテスト."""
    token_file = tmp_path / "token.json"
    token_file.write_text(json.dumps({"test": "data"}))

    with patch("share.auth.get_token_path", return_value=token_file):
        args = argparse.Namespace()
        result = auth.cmd_auth_logout(args)

    assert result == 0
    assert not token_file.exists()


def test_cmd_auth_dispatch_status():
    """--status フラグの振り分けテスト."""
    with patch("share.auth.cmd_auth_status", return_value=0) as mock_status:
        args = argparse.Namespace(status=True, logout=False)
        result = auth.cmd_auth_dispatch(args)
        mock_status.assert_called_once_with(args)
        assert result == 0


def test_cmd_auth_dispatch_logout():
    """--logout フラグの振り分けテスト."""
    with patch("share.auth.cmd_auth_logout", return_value=0) as mock_logout:
        args = argparse.Namespace(status=False, logout=True)
        result = auth.cmd_auth_dispatch(args)
        mock_logout.assert_called_once_with(args)
        assert result == 0


def test_load_token_invalid_json(tmp_path):
    """無効なJSONファイルのテスト."""
    from share.auth import _load_token

    bad_file = tmp_path / "token.json"
    bad_file.write_text("invalid json")
    with patch("share.auth.get_token_path", return_value=bad_file):
        assert _load_token() is None


def test_load_token_oserror(tmp_path):
    """ファイル読み込みエラーのテスト."""
    from share.auth import _load_token

    with patch("share.auth.get_token_path", return_value=tmp_path / "token.json"):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
                assert _load_token() is None


def test_cmd_auth_status_token_corrupted():
    """トークン破損時のテスト."""
    with patch("share.auth._load_token", return_value={"corrupted": True}):
        with patch("share.auth.get_client", return_value=None):
            args = argparse.Namespace()
            result = auth.cmd_auth_status(args)

    assert result == 1


def test_cmd_auth_status_auth_error():
    """AuthError時のテスト."""
    mock_client = MagicMock()
    mock_client.users_get_current_account.side_effect = dropbox.exceptions.AuthError(
        "req-id", "invalid_access_token"
    )

    with patch("share.auth._load_token", return_value={"valid": True}):
        with patch("share.auth.get_client", return_value=mock_client):
            args = argparse.Namespace()
            result = auth.cmd_auth_status(args)

    assert result == 1


def test_save_load_delete_token(tmp_path):
    """トークンの保存・読込・削除."""
    from share.auth import _save_token, _load_token, _delete_token

    token_path = tmp_path / "token.json"
    with patch("share.auth.get_token_path", return_value=token_path):
        data = {"app_key": "test", "refresh_token": "refresh"}

        _save_token(data)
        loaded = _load_token()
        assert loaded == data

        _delete_token()
        assert _load_token() is None


def test_cmd_auth_dispatch_default():
    """デフォルト（auth）フラグの振り分けテスト."""
    with patch("share.auth.cmd_auth", return_value=0) as mock_auth:
        args = argparse.Namespace(status=False, logout=False)
        result = auth.cmd_auth_dispatch(args)
        mock_auth.assert_called_once_with(args)
        assert result == 0


def test_cmd_auth_status_other_error():
    """予期しないエラーのテスト."""
    mock_client = MagicMock()
    mock_client.users_get_current_account.side_effect = Exception("Network Error")

    with patch("share.auth._load_token", return_value={"valid": True}):
        with patch("share.auth.get_client", return_value=mock_client):
            args = argparse.Namespace()
            result = auth.cmd_auth_status(args)

    assert result == 1
