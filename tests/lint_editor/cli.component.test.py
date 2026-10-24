# @path[tests/lint_editor/cli.component.test.py]

import pytest

from lint_editor import cli
from lint_editor.schema import Finding, ProgramError

# the exit codes pre-commit and shells depend on
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def test_main_returns_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "check_paths", lambda _paths: [])
    assert cli.main() == EXIT_OK


def test_main_returns_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "check_paths", lambda _paths: [Finding("a", "bad")])
    assert cli.main() == EXIT_FINDINGS


def test_main_returns_error_on_program_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_paths: list[str]) -> list[Finding]:
        message = "nope"
        raise ProgramError(message)

    monkeypatch.setattr(cli, "check_paths", boom)
    assert cli.main() == EXIT_ERROR
