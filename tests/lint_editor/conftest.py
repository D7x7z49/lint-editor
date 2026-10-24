# @path[tests/lint_editor/conftest.py]

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def base_config(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_editor/editorconfig/base/stdin.txt", ".editorconfig")


@pytest.fixture
def broken_config(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_editor/editorconfig/broken/stdin.txt", ".editorconfig")


@pytest.fixture
def inner_config(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_editor/editorconfig/inner/stdin.txt", "sub/.editorconfig")


@pytest.fixture
def mixed_attributes(copy_data: Callable[[str, str], Path]) -> Path:
    return copy_data("lint_editor/files/mixed/stdin.txt", ".gitattributes")
