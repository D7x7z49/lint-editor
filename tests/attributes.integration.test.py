# @path[tests/attributes.integration.test.py]

from collections.abc import Callable
from pathlib import Path

import pytest

from lint_editor.attributes import declared_non_text


def test_declared_non_text_reads_gitattributes(
    git_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    copy_data: Callable[[str, str], Path],
) -> None:
    copy_data("gitattributes/mixed", ".gitattributes")
    (git_repo / "a.png").write_bytes(b"\0")
    (git_repo / "b.txt").write_bytes(b"\0")
    (git_repo / "c.dat").write_bytes(b"\0")
    monkeypatch.chdir(git_repo)

    declared = declared_non_text([Path("a.png"), Path("b.txt"), Path("c.dat")])

    assert declared == {Path("a.png"), Path("b.txt")}
