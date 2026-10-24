# @path[tests/e2e/conftest.py]

import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

CASES = Path(__file__).parents[1] / "data" / "e2e"


@pytest.fixture
def e2e_case(git_repo: Path) -> Callable[..., Path]:
    # copy one case project into the temporary repository, then stage the paths
    def prepare(name: str, staged: Sequence[str] = ()) -> Path:
        source = CASES / name / "project"
        shutil.copytree(source, git_repo, dirs_exist_ok=True)
        if staged:
            subprocess.run(("git", "add", *staged), cwd=git_repo, check=True)
        return git_repo

    return prepare


@pytest.fixture
def run_cli() -> Callable[..., subprocess.CompletedProcess[str]]:
    # run a package module as the command line entry
    def run(repo: Path, module: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, "-m", module, *args),
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )

    return run
