"""ローカルファイルのアップロード機能（担当: Nakatani）.

コアロジック :func:`upload_file` は Dropbox クライアントを引数で受け取る純粋関数。
認証（Tani の ``get_client()``）とは疎結合にしてあり、IF が確定したら
:func:`cmd_upload` の取得部分を差し替えるだけで結合できる。
"""

from __future__ import annotations

import os

from dropbox.files import FileMetadata, WriteMode


def upload_file(dbx, local_path: str, dropbox_path: str | None = None,
                *, overwrite: bool = False) -> FileMetadata:
    """ローカルファイルを Dropbox にアップロードする.

    Args:
        dbx: Dropbox クライアント（``dropbox.Dropbox`` 互換。テストでは mock）。
        local_path: アップロードするローカルファイルのパス。
        dropbox_path: アップロード先の Dropbox パス。省略時はファイル名を
            ルート直下（``/<ファイル名>``）に配置する。
        overwrite: True なら既存ファイルを上書きする（既定は追加 / 自動リネーム）。

    Returns:
        アップロードされたファイルのメタデータ。

    Raises:
        FileNotFoundError: ローカルファイルが存在しない場合。
    """
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"ローカルファイルが見つかりません: {local_path}")

    if dropbox_path is None:
        dropbox_path = "/" + os.path.basename(local_path)

    mode = WriteMode("overwrite") if overwrite else WriteMode("add")

    with open(local_path, "rb") as f:
        return dbx.files_upload(f.read(), dropbox_path, mode=mode)


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
    # TODO(結合): Tani の認証 IF が確定したら get_client() に差し替える。
    from share.auth import get_client

    dbx = get_client()
    metadata = upload_file(dbx, args.local_path, args.dropbox_path,
                           overwrite=args.overwrite)
    print(f"アップロード完了: {metadata.path_display}")
    return 0
