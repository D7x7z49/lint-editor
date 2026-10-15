# @path[tests/conftest.py]

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def copy_data(tmp_path: Path) -> Callable[[str, str], Path]:
    # copy a fixture file from tests/data into the test temporary directory
    def copy(source: str, target: str) -> Path:
        destination = tmp_path / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((DATA_DIR / source).read_bytes())
        return destination

    return copy


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    # create an empty git repository at the test temporary directory
    subprocess.run(("git", "init"), cwd=tmp_path, check=True, capture_output=True)
    return tmp_path
