# @path[tests/cli.e2e.test.py]

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# the exit codes pre-commit and shells depend on
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def _run(repo: Path, *paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, "-m", "lint_editor", *paths),
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _setup(repo: Path, copy_data: Callable[[str, str], Path]) -> None:
    copy_data("editorconfig/base", ".editorconfig")
    copy_data("gitattributes/png", ".gitattributes")
    (repo / "good.txt").write_bytes(b"ok\n")
    (repo / "bad.txt").write_bytes(b"oops")
    (repo / "logo.png").write_bytes(b"\0")
    (repo / "data.bin").write_bytes(b"\0")


def test_end_to_end_reports_findings(
    git_repo: Path, copy_data: Callable[[str, str], Path]
) -> None:
    _setup(git_repo, copy_data)

    result = _run(git_repo, "good.txt", "bad.txt", "logo.png", "data.bin")

    assert result.returncode == EXIT_FINDINGS
    assert "bad.txt" in result.stderr
    assert "data.bin" in result.stderr
    assert "newline" in result.stderr
    assert "gitattributes" in result.stderr
    assert "good.txt" not in result.stderr
    assert "logo.png" not in result.stderr


def test_end_to_end_passes_a_clean_set(
    git_repo: Path, copy_data: Callable[[str, str], Path]
) -> None:
    _setup(git_repo, copy_data)

    result = _run(git_repo, "good.txt", "logo.png")

    assert result.returncode == EXIT_OK


def test_end_to_end_reports_a_program_error(
    git_repo: Path, copy_data: Callable[[str, str], Path]
) -> None:
    copy_data("editorconfig/broken", ".editorconfig")
    (git_repo / "good.txt").write_bytes(b"ok\n")

    result = _run(git_repo, "good.txt")

    assert result.returncode == EXIT_ERROR
    assert "lint-editor:" in result.stderr
    assert "Traceback" not in result.stderr


def test_end_to_end_requires_an_editorconfig(git_repo: Path) -> None:
    (git_repo / "good.txt").write_bytes(b"ok\n")

    result = _run(git_repo, "good.txt")

    assert result.returncode == EXIT_ERROR
    assert "editorconfig" in result.stderr
    assert "Traceback" not in result.stderr
