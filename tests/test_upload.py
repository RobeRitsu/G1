"""アップロード機能のユニットテスト（mock 利用）."""

from unittest.mock import MagicMock

import pytest
from dropbox.files import WriteMode

from share.cli import build_parser
from share.upload import cmd_upload, upload_file


def _make_dbx(path_display="/sample.txt"):
    """files_upload がメタデータ風オブジェクトを返す mock クライアントを作る."""
    dbx = MagicMock()
    dbx.files_upload.return_value = MagicMock(path_display=path_display)
    return dbx


def test_upload_file_calls_files_upload(tmp_path):
    local = tmp_path / "sample.txt"
    local.write_bytes(b"hello dropbox")
    dbx = _make_dbx()

    metadata = upload_file(dbx, str(local))

    dbx.files_upload.assert_called_once()
    args, kwargs = dbx.files_upload.call_args
    assert args[0] == b"hello dropbox"          # ファイル内容
    assert args[1] == "/sample.txt"             # 既定の Dropbox パス
    assert kwargs["mode"] == WriteMode("add")   # 既定は追加モード
    assert metadata.path_display == "/sample.txt"


def test_upload_file_uses_given_dropbox_path(tmp_path):
    local = tmp_path / "sample.txt"
    local.write_bytes(b"data")
    dbx = _make_dbx(path_display="/dir/renamed.txt")

    upload_file(dbx, str(local), "/dir/renamed.txt")

    args, _ = dbx.files_upload.call_args
    assert args[1] == "/dir/renamed.txt"


def test_upload_file_overwrite_mode(tmp_path):
    local = tmp_path / "sample.txt"
    local.write_bytes(b"data")
    dbx = _make_dbx()

    upload_file(dbx, str(local), overwrite=True)

    _, kwargs = dbx.files_upload.call_args
    assert kwargs["mode"] == WriteMode("overwrite")


def test_upload_file_missing_local_file_raises(tmp_path):
    dbx = _make_dbx()
    missing = tmp_path / "nope.txt"

    with pytest.raises(FileNotFoundError):
        upload_file(dbx, str(missing))

    dbx.files_upload.assert_not_called()


def test_parser_registers_upload_subcommand():
    parser = build_parser()
    args = parser.parse_args(["upload", "local.txt", "/remote.txt", "--overwrite"])

    assert args.command == "upload"
    assert args.local_path == "local.txt"
    assert args.dropbox_path == "/remote.txt"
    assert args.overwrite is True
    assert args.func is cmd_upload


def test_cmd_upload_not_authenticated():
    """未認証時のテスト."""
    import argparse
    from unittest.mock import patch

    with patch("share.client.get_client", return_value=None):
        args = argparse.Namespace(
            local_path="test.txt",
            dropbox_path=None,
            overwrite=False,
        )
        result = cmd_upload(args)
        assert result == 1


def test_parser_upload_defaults():
    parser = build_parser()
    args = parser.parse_args(["upload", "local.txt"])

    assert args.dropbox_path is None
    assert args.overwrite is False


def test_cmd_upload_success():
    """認証済みでアップロード成功."""
    import argparse
    from unittest.mock import MagicMock, patch

    mock_metadata = MagicMock()
    mock_metadata.path_display = "/uploaded.txt"

    with patch("share.client.get_client", return_value=MagicMock()):
        with patch("share.upload.upload_file", return_value=mock_metadata):
            args = argparse.Namespace(
                local_path="test.txt",
                dropbox_path=None,
                overwrite=False,
            )
            result = cmd_upload(args)
            assert result == 0


def test_cmd_upload_file_not_found():
    """認証済みだがローカルファイルが存在しない."""
    import argparse
    from unittest.mock import MagicMock, patch

    with patch("share.client.get_client", return_value=MagicMock()):
        with patch(
            "share.upload.upload_file",
            side_effect=FileNotFoundError("ローカルファイルが見つかりません: test.txt"),
        ):
            args = argparse.Namespace(
                local_path="test.txt",
                dropbox_path=None,
                overwrite=False,
            )
            result = cmd_upload(args)
            assert result == 1
