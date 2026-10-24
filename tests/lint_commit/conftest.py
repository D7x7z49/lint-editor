# @path[tests/lint_commit/conftest.py]

import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest


@pytest.fixture
def valid_config(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_commit/config/valid/stdin.txt", "valid.toml")


@pytest.fixture
def component_config(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_commit/config/component/stdin.txt", "component.toml")


@pytest.fixture
def commit_repo(
    git_repo: Path, component_config: Path
) -> Callable[[Sequence[str], str], Path]:
    # prepare a repository with the config, target paths, index, and message
    def setup(paths: Sequence[str], message: str) -> Path:
        shutil.copy(component_config, git_repo / "lint-commit.toml")
        for name in paths:
            target = git_repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n", encoding="utf-8")
        subprocess.run(("git", "add", *paths), cwd=git_repo, check=True)
        (git_repo / "msg.txt").write_text(message, encoding="utf-8")
        return git_repo

    return setup
