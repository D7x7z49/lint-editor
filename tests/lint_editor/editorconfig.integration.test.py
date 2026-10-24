# @path[tests/lint_editor/editorconfig.integration.test.py]

from pathlib import Path

import pytest

from lint_editor.editorconfig import check_text
from lint_editor.schema import ProgramError


@pytest.mark.usefixtures("base_config")
def test_check_text_reports_a_violation(tmp_path: Path) -> None:
    good = tmp_path / "good.txt"
    good.write_bytes(b"ok\n")
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"oops")

    assert check_text(good) == []
    assert check_text(bad) == ["file does not end with a newline"]


@pytest.mark.usefixtures("base_config", "inner_config")
def test_a_nearer_editorconfig_wins(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "a.txt"
    path.write_bytes(b"oops")

    # the inner file turns the final newline rule off
    assert check_text(path) == []


@pytest.mark.usefixtures("broken_config")
def test_check_text_reports_a_broken_editorconfig(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_bytes(b"ok\n")

    with pytest.raises(ProgramError):
        check_text(path)


def test_check_text_requires_a_matching_rule(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_bytes(b"ok\n")

    with pytest.raises(ProgramError):
        check_text(path)
