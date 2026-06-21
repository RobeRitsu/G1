"""コマンドラインのエントリポイント."""

import argparse
import logging
import sys

from share import auth, upload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="share", description="Dropbox 共有リンク発行ツール")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細なログを出力する")
    sub = parser.add_subparsers(dest="command", required=True)

    auth.add_auth_parser(sub)
    upload.add_upload_parser(sub)  # 実装済み
    # TODO: link, list, revoke のサブコマンドを追加

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
