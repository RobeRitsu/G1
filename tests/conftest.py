"""テスト共通 Fixture."""

import json

import pytest


@pytest.fixture
def tmp_token_file(tmp_path):
    """一時的なトークンファイルを作成する Fixture.

    Returns:
        Path: トークンファイルのパス
    """
    token_path = tmp_path / "token.json"
    data = {
        "app_key": "test_key",
        "refresh_token": "test_refresh_token",
        "account_id": "dbid:test123",
    }
    token_path.write_text(json.dumps(data))
    return token_path
