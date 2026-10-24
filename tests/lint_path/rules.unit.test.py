# @path[tests/lint_path/rules.unit.test.py]

from pathlib import Path

import pytest

from lint_path.rules import parse_contract
from lint_path.schema import PathContract, PathContractError

HASH_LENGTH = 7
EXPECTED_RULES = 2


def parse(text: str, tmp_path: Path) -> PathContract:
    return parse_contract(text, tmp_path / ".pathbase", tmp_path)


def test_default_mode(tmp_path: Path) -> None:
    contract = parse("/a\n", tmp_path)
    rule = contract.rules[0]
    assert rule.mode == "allow"
    assert len(rule.name) == HASH_LENGTH


def test_require(tmp_path: Path) -> None:
    contract = parse("# $name = index\n# $mode = require\n/a\n", tmp_path)
    rule = contract.rules[0]
    assert rule.mode == "require"
    assert rule.name == "index"


def test_unknown_key(tmp_path: Path) -> None:
    with pytest.raises(PathContractError, match="unknown key"):
        parse("# $nope = 1\n/a\n", tmp_path)


def test_orphan_control(tmp_path: Path) -> None:
    with pytest.raises(PathContractError, match="control without a rule"):
        parse("# $name = x\n", tmp_path)


def test_import(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pathbase"
    shared.write_text("# $set_name = shared\n/a\n", encoding="utf-8")
    contract = parse("# @import shared.pathbase\n/b\n", tmp_path)
    assert len(contract.rules) == EXPECTED_RULES
    assert contract.imports["shared"] == str(tmp_path)


def test_import_override(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pathbase"
    shared.write_text("# $set_name = shared\n# $name = a\n/a\n", encoding="utf-8")
    contract = parse("# @import shared.pathbase\n# $name = a\n/b\n", tmp_path)
    assert len(contract.rules) == 1
    assert contract.rules[0].name == "a"


def test_cross_domain_override(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pathbase"
    shared.write_text("# $set_name = shared\n# $name = a\n/a\n", encoding="utf-8")
    contract = parse("# @import shared.pathbase\n# $name = shared.a\n/b\n", tmp_path)
    assert len(contract.rules) == 1
    assert contract.rules[0].name == "shared.a"


def test_import_alias(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pathbase"
    shared.write_text("# $set_name = shared\n/a\n", encoding="utf-8")
    contract = parse("# @import shared.pathbase as other\n/b\n", tmp_path)
    assert "other" in contract.imports


def test_projection_unknown_rule(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pathbase"
    shared.write_text("# $set_name = shared\n/a\n", encoding="utf-8")
    with pytest.raises(PathContractError, match="unknown rule"):
        parse(
            "# @require shared.pathbase\n# $projection = @shared:nope\n/b\n",
            tmp_path,
        )


def test_import_cycle(tmp_path: Path) -> None:
    first = tmp_path / "a.pathbase"
    second = tmp_path / "b.pathbase"
    first.write_text("# $set_name = a\n# @import b.pathbase\n/x\n", encoding="utf-8")
    second.write_text("# $set_name = b\n# @import a.pathbase\n/y\n", encoding="utf-8")
    with pytest.raises(PathContractError, match="in a cycle"):
        parse(first.read_text(encoding="utf-8"), tmp_path)


def test_require_last_group(tmp_path: Path) -> None:
    with pytest.raises(PathContractError, match="single segment"):
        parse("# $mode = require\n/mods/(a/b)/\n", tmp_path)


def test_limit_invalid(tmp_path: Path) -> None:
    with pytest.raises(PathContractError, match="invalid value"):
        parse("# $depth_max = many\n/a\n", tmp_path)
