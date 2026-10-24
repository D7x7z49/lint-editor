# @path[tests/lint_commit/cli.component.test.py]

import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from lint_commit import cli

BODY = "\n".join(f"- entry {index}" for index in range(5))
DESCRIPTION = "add a parser for the nested arrays"

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_ERROR = 2

Repo = Callable[[Sequence[str], str], Path]


def run_cli(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["lint-commit", *args])
    return cli.main()


def test_passing_commit(commit_repo: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = commit_repo(["src/api/a.py"], f"feat(api): {DESCRIPTION}\n\n{BODY}\n")
    monkeypatch.chdir(repo)
    args = ["--config", "commit-config.toml", "msg.txt"]
    assert run_cli(monkeypatch, args) == EXIT_OK


def test_split_is_rejected(commit_repo: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = ["src/api/a.py", "docs/b.md"]
    repo = commit_repo(paths, f"feat: {DESCRIPTION}\n\n{BODY}\n")
    monkeypatch.chdir(repo)
    args = ["--config", "commit-config.toml", "msg.txt"]
    assert run_cli(monkeypatch, args) == EXIT_REJECTED


def test_uncovered_path_is_rejected(
    commit_repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = commit_repo(["vendor/a.js"], f"chore: {DESCRIPTION}\n\n{BODY}\n")
    monkeypatch.chdir(repo)
    args = ["--config", "commit-config.toml", "msg.txt"]
    assert run_cli(monkeypatch, args) == EXIT_REJECTED


def test_missing_config_is_a_tool_error(
    commit_repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = commit_repo(["src/a.py"], f"feat(src): {DESCRIPTION}\n")
    (repo / "commit-config.toml").unlink()
    monkeypatch.chdir(repo)
    args = ["--config", "commit-config.toml", "msg.txt"]
    assert run_cli(monkeypatch, args) == EXIT_ERROR


def test_fixup_commit_is_skipped(
    commit_repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = commit_repo(["src/a.py"], "fixup! feat: add\n")
    (repo / "commit-config.toml").unlink()
    monkeypatch.chdir(repo)
    args = ["--config", "commit-config.toml", "msg.txt"]
    assert run_cli(monkeypatch, args) == EXIT_OK
