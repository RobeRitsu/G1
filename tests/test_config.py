"""設定・環境変数のテスト."""

from unittest.mock import patch


def test_get_data_dir_windows(monkeypatch):
    """Windows のデータディレクトリ."""
    monkeypatch.setenv("LOCALAPPDATA", "C:/Users/Test/AppData/Local")
    with patch("platform.system", return_value="Windows"):
        from share.config import get_data_dir
        path = get_data_dir()
        assert "AppData" in str(path)
        assert path.name == "share-cli"


def test_get_data_dir_linux(monkeypatch):
    """Linux のデータディレクトリ."""
    monkeypatch.setenv("XDG_DATA_HOME", "/home/test/.local/share")
    with patch("platform.system", return_value="Linux"):
        from share.config import get_data_dir
        path = get_data_dir()
        assert str(path).replace("\\", "/").endswith(".local/share/share-cli")


def test_get_data_dir_mac(monkeypatch):
    """Mac のデータディレクトリ."""
    with patch("platform.system", return_value="Darwin"):
        from share.config import get_data_dir
        path = get_data_dir()
        assert "Application Support" in str(path)
        assert path.name == "share-cli"


def test_get_data_dir_default():
    """環境変数未設定時のデフォルト."""
    with patch("platform.system", return_value="Linux"):
        from share.config import get_data_dir
        path = get_data_dir()
        assert path.name == "share-cli"


def test_get_token_path():
    """トークンパスのテスト."""
    from share.config import get_token_path
    path = get_token_path()
    assert path.name == "token.json"
    assert path.parent.name == "share-cli"
