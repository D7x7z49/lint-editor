# @path[tests/e2e/lint_editor/cli.e2e.test.py]

import subprocess
from collections.abc import Callable
from pathlib import Path

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def test_end_to_end_reports_findings(
    e2e_case: Callable[..., Path],
    run_cli: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    repo = e2e_case("lint_editor/reports-findings")
    result = run_cli(repo, "lint_editor", "good.txt", "bad.txt", "logo.png", "data.bin")

    assert result.returncode == EXIT_FINDINGS
    assert "bad.txt" in result.stderr
    assert "data.bin" in result.stderr
    assert "newline" in result.stderr
    assert "gitattributes" in result.stderr
    assert "good.txt" not in result.stderr
    assert "logo.png" not in result.stderr


def test_end_to_end_passes_a_clean_set(
    e2e_case: Callable[..., Path],
    run_cli: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    repo = e2e_case("lint_editor/clean-set")
    result = run_cli(repo, "lint_editor", "good.txt", "logo.png")

    assert result.returncode == EXIT_OK


def test_end_to_end_reports_a_program_error(
    e2e_case: Callable[..., Path],
    run_cli: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    repo = e2e_case("lint_editor/program-error")
    result = run_cli(repo, "lint_editor", "good.txt")

    assert result.returncode == EXIT_ERROR
    assert "[lint-editor]" in result.stderr
    assert "Traceback" not in result.stderr


def test_end_to_end_requires_an_editorconfig(
    e2e_case: Callable[..., Path],
    run_cli: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    repo = e2e_case("lint_editor/requires-editorconfig")
    result = run_cli(repo, "lint_editor", "good.txt")

    assert result.returncode == EXIT_ERROR
    assert "editorconfig" in result.stderr
    assert "Traceback" not in result.stderr
