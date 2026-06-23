"""ローカルファイルのアップロード機能（担当: Nakatani）.

コアロジック :func:`upload_file` は Dropbox クライアントを引数で受け取る純粋関数。
認証（Tani の ``get_client()``）とは疎結合にしてあり、IF が確定したら
:func:`cmd_upload` の取得部分を差し替えるだけで結合できる。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from dropbox.files import (
    CommitInfo,
    FileMetadata,
    UploadSessionCursor,
    WriteMode,
)

# 1 チャンクあたりの読み込みサイズ（8MB）。
# files_upload は Dropbox API 上 150MB が上限のため、これを超えるファイルは
# アップロードセッション（分割アップロード）に切り替える。チャンク単位で
# 読み書きするのでファイル全体をメモリに載せず、大ファイルでも安全。
CHUNK_SIZE = 8 * 1024 * 1024


def upload_file(dbx, local_path: str, dropbox_path: str | None = None,
                *, overwrite: bool = False,
                on_progress: Callable[[int, int], None] | None = None) -> FileMetadata:
    """ローカルファイルを Dropbox にアップロードする.

    ``CHUNK_SIZE`` 以下のファイルは ``files_upload`` で 1 回送信する。
    それを超えるファイルはアップロードセッションを使い、``CHUNK_SIZE`` ごとに
    分割して送信する。これにより 150MB の API 制限を回避し、ファイル全体を
    メモリへ読み込まないため大ファイルでもメモリ安全。

    Args:
        dbx: Dropbox クライアント（``dropbox.Dropbox`` 互換。テストでは mock）。
        local_path: アップロードするローカルファイルのパス。
        dropbox_path: アップロード先の Dropbox パス。省略時はファイル名を
            ルート直下（``/<ファイル名>``）に配置する。
        overwrite: True なら既存ファイルを上書きする（既定は追加 / 自動リネーム）。
        on_progress: 進捗コールバック。``(送信済みバイト数, 総バイト数)`` で呼ばれる。
            セッション方式（大ファイル）でのみ各チャンク送信後に呼ばれる。

    Returns:
        アップロードされたファイルのメタデータ。

    Raises:
        FileNotFoundError: ローカルファイルが存在しない場合。
    """
    local = Path(local_path)
    if not local.is_file():
        raise FileNotFoundError(f"ローカルファイルが見つかりません: {local_path}")

    if dropbox_path is None:
        dropbox_path = "/" + local.name

    mode = WriteMode("overwrite") if overwrite else WriteMode("add")
    file_size = local.stat().st_size

    with local.open("rb") as f:
        if file_size <= CHUNK_SIZE:
            return dbx.files_upload(f.read(), dropbox_path, mode=mode)
        return _upload_session(dbx, f, dropbox_path, mode, file_size, on_progress)


def _upload_session(dbx, f, dropbox_path: str, mode: WriteMode,
                    file_size: int,
                    on_progress: Callable[[int, int], None] | None) -> FileMetadata:
    """アップロードセッションを使ってファイルを分割送信する."""
    session = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
    cursor = UploadSessionCursor(session_id=session.session_id, offset=f.tell())
    commit = CommitInfo(path=dropbox_path, mode=mode)
    if on_progress is not None:
        on_progress(f.tell(), file_size)

    # 残りが 1 チャンク以下になるまで append で送信し、最後の塊を finish で確定する。
    while file_size - f.tell() > CHUNK_SIZE:
        dbx.files_upload_session_append_v2(f.read(CHUNK_SIZE), cursor)
        cursor.offset = f.tell()
        if on_progress is not None:
            on_progress(f.tell(), file_size)

    metadata = dbx.files_upload_session_finish(f.read(CHUNK_SIZE), cursor, commit)
    if on_progress is not None:
        on_progress(file_size, file_size)
    return metadata


def add_upload_parser(subparsers) -> None:
    """``share upload`` サブコマンドを登録する."""
    parser = subparsers.add_parser("upload", help="ローカルファイルを Dropbox にアップロードする")
    parser.add_argument("local_path", help="アップロードするローカルファイルのパス")
    parser.add_argument("dropbox_path", nargs="?", default=None,
                        help="アップロード先の Dropbox パス（省略時は /<ファイル名>）")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="既存ファイルを上書きする")
    parser.set_defaults(func=cmd_upload)


def cmd_upload(args) -> int:
    """``share upload`` のハンドラ."""
    from share.client import get_client

    dbx = get_client()
    if dbx is None:
        print("エラー: 認証が必要です。")
        print("'share auth' を実行してください。")
        return 1

    def show_progress(sent: int, total: int) -> None:
        pct = sent * 100 // total if total else 100
        end = "\n" if sent >= total else ""
        print(f"\rアップロード中: {pct}% ({sent}/{total} バイト)", end=end, flush=True)

    try:
        metadata = upload_file(dbx, args.local_path, args.dropbox_path,
                               overwrite=args.overwrite, on_progress=show_progress)
    except FileNotFoundError as exc:
        print(f"エラー: {exc}")
        return 1

    print(f"アップロード完了: {metadata.path_display}")
    return 0
