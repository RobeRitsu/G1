"""CLIエントリポイントのテスト."""

from unittest.mock import MagicMock, patch

from share.cli import build_parser, main


def test_build_parser():
    """パーサー構築テスト."""
    parser = build_parser()
    assert parser._subparsers is not None


def test_main():
    """main() 関数のテスト."""
    with patch("share.cli.build_parser") as mock_build:
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.func.return_value = 0
        mock_args.verbose = False
        mock_parser.parse_args.return_value = mock_args
        mock_build.return_value = mock_parser

        result = main()
        assert result == 0


def test_main_verbose():
    """main() --verbose パスのテスト."""
    with patch("share.cli.build_parser") as mock_build:
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.func.return_value = 0
        mock_args.verbose = True
        mock_parser.parse_args.return_value = mock_args
        mock_build.return_value = mock_parser

        result = main()
        assert result == 0
