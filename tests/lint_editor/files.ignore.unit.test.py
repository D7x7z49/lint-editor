# @path[tests/lint_editor/files.ignore.unit.test.py]

from pathlib import Path

import pytest

from lint_editor.files import find_ignore_files, is_ignored, load_ignore
from lint_editor.schema import ProgramError


def write(root: Path, text: str) -> Path:
    path = root / "lint-editor.ignore"
    path.write_text(text, encoding="utf-8")
    return path


def write_config(root: Path, text: str) -> Path:
    directory = root / "config"
    directory.mkdir()
    path = directory / "lint-editor.ignore"
    path.write_text(text, encoding="utf-8")
    return path


def test_missing_file_excludes_nothing(tmp_path: Path) -> None:
    spec = load_ignore(())
    assert not is_ignored(spec, tmp_path, tmp_path / "src/a.py")


def test_pattern_matches_a_directory(tmp_path: Path) -> None:
    path = write(tmp_path, "tests/data/\n")
    spec = load_ignore([path])
    assert is_ignored(spec, tmp_path, tmp_path / "tests/data/a.txt")


def test_comments_and_blank_lines(tmp_path: Path) -> None:
    path = write(tmp_path, "# comment\n\nsrc/*.py\n")
    spec = load_ignore([path])
    assert is_ignored(spec, tmp_path, tmp_path / "src/a.py")


def test_unmatched_path_passes(tmp_path: Path) -> None:
    path = write(tmp_path, "tests/data/\n")
    spec = load_ignore([path])
    assert not is_ignored(spec, tmp_path, tmp_path / "src/a.py")


def test_negated_pattern_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "!src/a.py\n")
    with pytest.raises(ProgramError, match="negated"):
        load_ignore([path])


def test_absolute_path_is_relative_to_root(tmp_path: Path) -> None:
    path = write(tmp_path, "tests/data/\n")
    spec = load_ignore([path])
    target = (tmp_path / "tests/data/a.txt").resolve()
    assert is_ignored(spec, tmp_path, target)


def test_find_the_root_file(tmp_path: Path) -> None:
    path = write(tmp_path, "src/*.py\n")
    assert find_ignore_files(tmp_path) == (path,)


def test_find_the_config_file(tmp_path: Path) -> None:
    path = write_config(tmp_path, "tests/data/\n")
    assert find_ignore_files(tmp_path) == (path,)


def test_find_both_files(tmp_path: Path) -> None:
    root = write(tmp_path, "src/*.py\n")
    config = write_config(tmp_path, "tests/data/\n")
    assert find_ignore_files(tmp_path) == (root, config)


def test_two_files_are_merged(tmp_path: Path) -> None:
    write(tmp_path, "src/*.py\n")
    write_config(tmp_path, "tests/data/\n")
    spec = load_ignore(find_ignore_files(tmp_path))
    assert is_ignored(spec, tmp_path, tmp_path / "src/a.py")
    assert is_ignored(spec, tmp_path, tmp_path / "tests/data/a.txt")
