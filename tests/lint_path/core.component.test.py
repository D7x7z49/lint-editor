# @path[tests/lint_path/core.component.test.py]

from pathlib import Path

from lint_path.core import audit, gate, judge
from lint_path.rules import load_contract


def make(tmp_path: Path, text: str) -> None:
    (tmp_path / ".pathbase").write_text(text, encoding="utf-8")


def test_judge_allow(tmp_path: Path) -> None:
    make(tmp_path, "/a\n")
    (tmp_path / "a").touch()
    contract = load_contract(tmp_path / ".pathbase")
    assert judge(contract, tmp_path / "a").allowed


def test_judge_deny(tmp_path: Path) -> None:
    make(tmp_path, "/a\n")
    (tmp_path / "b").touch()
    contract = load_contract(tmp_path / ".pathbase")
    assert not judge(contract, tmp_path / "b").allowed


def test_gate_deny(tmp_path: Path) -> None:
    make(tmp_path, "/a\n")
    assert not gate(tmp_path / "b", tmp_path).allowed


def test_audit_reports(tmp_path: Path) -> None:
    make(tmp_path, "/a\n")
    (tmp_path / "b").touch()
    assert audit(tmp_path)


def test_require_each_sibling(tmp_path: Path) -> None:
    make(
        tmp_path,
        "/mods/\n/mods/*/\n\n# $name = index\n# $mode = require\n/mods/*/index.py\n",
    )
    (tmp_path / "mods" / "a").mkdir(parents=True)
    findings = audit(tmp_path)
    assert any("index" in finding.reason for finding in findings)


def test_require_satisfied(tmp_path: Path) -> None:
    make(
        tmp_path,
        "/mods/\n/mods/*/\n\n# $name = index\n# $mode = require\n/mods/*/index.py\n",
    )
    (tmp_path / "mods" / "a").mkdir(parents=True)
    (tmp_path / "mods" / "a" / "index.py").touch()
    assert not audit(tmp_path)


def test_projection(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / ".pathbase").write_text(
        "# $set_name = src\n\n# $name = source\n/a.py\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / ".pathbase").write_text(
        "# $set_name = tests\n"
        "# @require ../src\n"
        "\n"
        "# $name = test\n"
        "# $projection = @src:source >> s|\\.test\\.py$|.py|\n"
        "/a.test.py\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "a.py").touch()
    (tmp_path / "tests" / "a.test.py").touch()
    findings = audit(tmp_path)
    assert not findings, findings


def test_projection_missing_source(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / ".pathbase").write_text(
        "# $set_name = src\n\n# $name = source\n/a.py\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / ".pathbase").write_text(
        "# $set_name = tests\n"
        "# @require ../src\n"
        "\n"
        "# $name = test\n"
        "# $projection = @src:source >> s|\\.test\\.py$|.py|\n"
        "/a.test.py\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "a.test.py").touch()
    assert any("no rule matches" in finding.reason for finding in audit(tmp_path))


def test_capacity_depth(tmp_path: Path) -> None:
    (tmp_path / ".pathbase").write_text("# $depth_max = 1\n/**\n", encoding="utf-8")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").touch()
    assert any("depth_max" in finding.reason for finding in audit(tmp_path))


def test_require_namespace(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / ".pathbase").write_text(
        "# $set_name = src\n/a\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / ".pathbase").write_text(
        "# @require ../src\n/b\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "b").touch()
    contract = load_contract(tmp_path / "tests" / ".pathbase")
    assert contract.imports["src"] == str(tmp_path / "src")


def test_capacity_degree(tmp_path: Path) -> None:
    make(tmp_path, "# $degree_max = 1\n/**\n")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").touch()
    (tmp_path / "a" / "c").touch()
    assert any("degree_max" in finding.reason for finding in audit(tmp_path))


def test_capacity_node(tmp_path: Path) -> None:
    make(tmp_path, "# $node_max = 1\n/**\n")
    (tmp_path / "a").touch()
    (tmp_path / "b").touch()
    assert any("node_max" in finding.reason for finding in audit(tmp_path))
