# @path[tests/lint_path/cli.component.test.py]

from pathlib import Path

from lint_path.cli import run


def test_run_ok(tmp_path: Path) -> None:
    (tmp_path / ".pathbase").write_text("/a\n", encoding="utf-8")
    (tmp_path / "a").touch()
    assert run(["--root", str(tmp_path), "--audit"]) == 0


def test_run_reject(tmp_path: Path) -> None:
    (tmp_path / ".pathbase").write_text("/a\n", encoding="utf-8")
    (tmp_path / "b").touch()
    assert run(["--root", str(tmp_path), "--audit"]) == 1


def test_run_missing_contract(tmp_path: Path) -> None:
    assert run(["--root", str(tmp_path), "--audit"]) == 0
