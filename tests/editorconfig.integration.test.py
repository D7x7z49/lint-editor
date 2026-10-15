# @path[tests/editorconfig.integration.test.py]

from collections.abc import Callable
from pathlib import Path

import pytest

from lint_editor.editorconfig import check_text
from lint_editor.errors import ProgramError


def test_check_text_reports_a_violation(
    tmp_path: Path, copy_data: Callable[[str, str], Path]
) -> None:
    copy_data("editorconfig/base", ".editorconfig")
    good = tmp_path / "good.txt"
    good.write_bytes(b"ok\n")
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"oops")

    assert check_text(good) == []
    assert check_text(bad) == ["file does not end with a newline"]


def test_a_nearer_editorconfig_wins(
    tmp_path: Path, copy_data: Callable[[str, str], Path]
) -> None:
    copy_data("editorconfig/base", ".editorconfig")
    copy_data("editorconfig/inner", "sub/.editorconfig")
    path = tmp_path / "sub" / "a.txt"
    path.write_bytes(b"oops")

    # the inner file turns the final newline rule off
    assert check_text(path) == []


def test_check_text_reports_a_broken_editorconfig(
    tmp_path: Path, copy_data: Callable[[str, str], Path]
) -> None:
    copy_data("editorconfig/broken", ".editorconfig")
    path = tmp_path / "a.txt"
    path.write_bytes(b"ok\n")

    with pytest.raises(ProgramError):
        check_text(path)


def test_check_text_requires_a_matching_rule(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_bytes(b"ok\n")

    with pytest.raises(ProgramError):
        check_text(path)
