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


def test_small_file_does_not_use_session(tmp_path, monkeypatch):
    """CHUNK_SIZE 以下のファイルはセッションを使わず files_upload で送る."""
    import share.upload as upload_mod

    monkeypatch.setattr(upload_mod, "CHUNK_SIZE", 8)  # 8 バイト
    local = tmp_path / "small.bin"
    local.write_bytes(b"12345678")  # ちょうど 8 バイト（境界）
    dbx = _make_dbx()

    upload_file(dbx, str(local))

    dbx.files_upload.assert_called_once()
    dbx.files_upload_session_start.assert_not_called()


def test_large_file_uses_upload_session(tmp_path, monkeypatch):
    """CHUNK_SIZE を超えるファイルはセッションで分割アップロードする."""
    import share.upload as upload_mod

    monkeypatch.setattr(upload_mod, "CHUNK_SIZE", 4)  # 4 バイト/チャンク
    local = tmp_path / "large.bin"
    local.write_bytes(b"0123456789")  # 10 バイト -> 4+4+2 の 3 チャンク
    dbx = MagicMock()
    dbx.files_upload_session_start.return_value = MagicMock(session_id="sid")
    dbx.files_upload_session_finish.return_value = MagicMock(path_display="/large.bin")

    progress = []
    metadata = upload_file(dbx, str(local),
                           on_progress=lambda sent, total: progress.append((sent, total)))

    # 単発アップロードは使わない
    dbx.files_upload.assert_not_called()
    # start(最初の4B) -> append(次の4B) -> finish(残り2B)
    dbx.files_upload_session_start.assert_called_once_with(b"0123")
    dbx.files_upload_session_append_v2.assert_called_once()
    append_args, _ = dbx.files_upload_session_append_v2.call_args
    assert append_args[0] == b"4567"
    finish_args, _ = dbx.files_upload_session_finish.call_args
    assert finish_args[0] == b"89"
    assert metadata.path_display == "/large.bin"
    # 進捗は最終的に 10/10 に到達する
    assert progress[-1] == (10, 10)


def test_large_file_session_uses_dropbox_path_and_mode(tmp_path, monkeypatch):
    """セッション方式でも dropbox_path と overwrite モードが commit に渡る."""
    import share.upload as upload_mod
    from dropbox.files import CommitInfo

    monkeypatch.setattr(upload_mod, "CHUNK_SIZE", 4)
    local = tmp_path / "large.bin"
    local.write_bytes(b"0123456789")
    dbx = MagicMock()
    dbx.files_upload_session_start.return_value = MagicMock(session_id="sid")

    upload_file(dbx, str(local), "/dir/dest.bin", overwrite=True)

    _, finish_kwargs = dbx.files_upload_session_finish.call_args
    finish_args, _ = dbx.files_upload_session_finish.call_args
    commit = finish_args[2]
    assert isinstance(commit, CommitInfo)
    assert commit.path == "/dir/dest.bin"
    assert commit.mode == WriteMode("overwrite")
