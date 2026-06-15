"""コマンドラインのエントリポイント（土台）.

各サブコマンドの中身は担当者が実装する。
"""

import argparse
import sys

from share.upload import add_upload_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="share", description="Dropbox 共有リンク発行ツール")
    sub = parser.add_subparsers(dest="command", required=True)

    # TODO(担当者): 各サブコマンドを追加し、set_defaults(func=...) でハンドラを紐づける
    # 例) sub.add_parser("auth", help="Dropbox 認証を行う").set_defaults(func=cmd_auth)
    add_upload_parser(sub)  # アップロード（Nakatani）

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
