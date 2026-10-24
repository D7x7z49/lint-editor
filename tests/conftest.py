# @path[tests/conftest.py]

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture
def copy_data(tmp_path: Path, data_dir: Path) -> Callable[[str, str], Path]:
    # copy one data file into the test temporary directory
    def copy(case: str, target: str) -> Path:
        destination = tmp_path / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((data_dir / case).read_bytes())
        return destination

    return copy


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    # create an empty git repository at the test temporary directory
    subprocess.run(("git", "init"), cwd=tmp_path, check=True, capture_output=True)
    return tmp_path
