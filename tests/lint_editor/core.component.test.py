# @path[tests/lint_editor/core.component.test.py]

from pathlib import Path

import pytest

from lint_editor import core


def test_text_file_routes_to_editorconfig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a.txt"
    path.write_text("ok\n")
    monkeypatch.setattr(core, "declared_non_text", lambda _paths: set())
    monkeypatch.setattr(core, "check_text", lambda _p: ["boom"])
    findings = core.check_paths([str(path)])
    assert findings == [core.Finding(str(path), "boom")]


def test_non_text_file_needs_a_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"\0")
    monkeypatch.setattr(core, "declared_non_text", lambda _paths: set())
    monkeypatch.setattr(core, "check_text", lambda _p: [])
    findings = core.check_paths([str(path)])
    assert findings == [
        core.Finding(str(path), "non-text file without a .gitattributes declaration")
    ]


def test_declared_non_text_file_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"\0")
    monkeypatch.setattr(core, "declared_non_text", lambda _paths: {Path(str(path))})
    monkeypatch.setattr(core, "check_text", lambda _p: [])
    assert core.check_paths([str(path)]) == []


def test_missing_path_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(core, "declared_non_text", lambda _paths: set())
    assert core.check_paths([str(tmp_path / "nope")]) == []
