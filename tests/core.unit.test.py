# @path[tests/core.unit.test.py]

from pathlib import Path

from lint_editor.core import is_binary


def test_empty_file_is_text(tmp_path: Path) -> None:
    path = tmp_path / "empty"
    path.write_bytes(b"")
    assert not is_binary(path)


def test_nul_inside_the_window_is_binary(tmp_path: Path) -> None:
    path = tmp_path / "early"
    path.write_bytes(b"abc\0def")
    assert is_binary(path)


def test_nul_at_offset_7999_is_binary(tmp_path: Path) -> None:
    # the last byte git reads when it sniffs a file
    path = tmp_path / "edge"
    path.write_bytes(b"x" * 7999 + b"\0")
    assert is_binary(path)


def test_nul_at_offset_8000_is_text(tmp_path: Path) -> None:
    # the first byte git does not read when it sniffs a file
    path = tmp_path / "edge"
    path.write_bytes(b"x" * 8000 + b"\0")
    assert not is_binary(path)
