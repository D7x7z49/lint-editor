# @path[tests/lint_editor/cli.component.test.py]

import sys

import pytest

from lint_editor import cli
from lint_editor.schema import Finding, ProgramError

# the exit codes pre-commit and shells depend on
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def run_main(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["lint-editor", *args])
    return cli.main()


def test_main_returns_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "check_paths", lambda _paths, _ignore_files: [])
    assert run_main(monkeypatch, ["a.txt"]) == EXIT_OK


def test_main_returns_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli, "check_paths", lambda _paths, _ignore_files: [Finding("a", "bad")]
    )
    assert run_main(monkeypatch, ["a.txt"]) == EXIT_FINDINGS


def test_main_returns_error_on_program_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_paths: list[str], _ignore_files: list[str] | None) -> list[Finding]:
        message = "nope"
        raise ProgramError(message)

    monkeypatch.setattr(cli, "check_paths", boom)
    assert run_main(monkeypatch, ["a.txt"]) == EXIT_ERROR


def test_main_passes_ignore_files(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def capture(paths: list[str], ignore_files: list[str] | None) -> list[Finding]:
        seen["paths"] = paths
        seen["ignore_files"] = ignore_files
        return []

    monkeypatch.setattr(cli, "check_paths", capture)
    args = ["--ignore-file", "first", "--ignore-file", "second", "a.txt"]
    assert run_main(monkeypatch, args) == EXIT_OK
    assert seen["ignore_files"] == ["first", "second"]
    assert seen["paths"] == ["a.txt"]
