# @path[tests/lint_commit/rules.unit.test.py]

from pathlib import Path

import pytest

from lint_commit.rules import Matcher, find_config, load_config
from lint_commit.schema import CommitRule, ProgramError

MINIMAL = """
[types]
feat = "a feature"

[rules]
"**" = ["feat"]
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "lint-commit.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_config(valid_config: Path) -> None:
    config = load_config(valid_config)
    assert [rule.path for rule in config.commit_rule] == ["**", "src/**"]
    assert config.commit_rule[1].types == ("feat", "fix")
    assert config.commit_type["feat"] == "a feature"


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ProgramError, match="no configuration file"):
        load_config(tmp_path / "absent.toml")


def test_missing_types_table(tmp_path: Path) -> None:
    text = '[rules]\n"**" = ["feat"]\n'
    with pytest.raises(ProgramError, match=r"\[types\]"):
        load_config(write(tmp_path, text))


def test_missing_rules_table(tmp_path: Path) -> None:
    text = '[types]\nfeat = "a feature"\n'
    with pytest.raises(ProgramError, match=r"\[rules\]"):
        load_config(write(tmp_path, text))


def test_unknown_type_in_types_table(tmp_path: Path) -> None:
    text = '[types]\nfeatx = "x"\n\n[rules]\n"**" = ["feat"]\n'
    with pytest.raises(ProgramError, match="unknown type"):
        load_config(write(tmp_path, text))


def test_unknown_type_in_rule(tmp_path: Path) -> None:
    text = '[types]\nfeat = "a feature"\n\n[rules]\n"**" = ["featx"]\n'
    with pytest.raises(ProgramError, match="unknown type"):
        load_config(write(tmp_path, text))


def test_empty_rule_types(tmp_path: Path) -> None:
    text = '[types]\nfeat = "a feature"\n\n[rules]\n"**" = []\n'
    with pytest.raises(ProgramError, match="non-empty"):
        load_config(write(tmp_path, text))


def test_empty_rules(tmp_path: Path) -> None:
    text = '[types]\nfeat = "a feature"\n\n[rules]\n'
    with pytest.raises(ProgramError, match="must not be empty"):
        load_config(write(tmp_path, text))


def test_unexpected_top_key(tmp_path: Path) -> None:
    text = 'extra = true\n\n[types]\nfeat = "a feature"\n\n[rules]\n"**" = ["feat"]\n'
    with pytest.raises(ProgramError, match="unexpected top key"):
        load_config(write(tmp_path, text))


def test_broken_toml(tmp_path: Path) -> None:
    with pytest.raises(ProgramError, match="lint-commit"):
        load_config(write(tmp_path, "rules = [\n"))


def test_builtin_reference_marks_are_loaded(valid_config: Path) -> None:
    config = load_config(valid_config)
    marks = [spec.mark for spec in config.reference]
    assert "REFERENCE-LINK" in marks
    assert "REFERENCE-GITHUB" in marks
    assert "REFERENCE-GITLAB" in marks
    assert "REFERENCE-COMMIT" in marks
    assert "REFERENCE-FILE" in marks


def test_reference_entry_overrides_builtin(tmp_path: Path, valid_config: Path) -> None:
    text = valid_config.read_text(encoding="utf-8")
    text += "\n[reference]\n\"LINK\" = '^https://example\\.com/\\S+$'\n"
    config = load_config(write(tmp_path, text))
    link = next(spec for spec in config.reference if spec.mark == "REFERENCE-LINK")
    assert link.pattern.pattern == r"^https://example\.com/\S+$"


def test_reference_entry_is_added(tmp_path: Path, valid_config: Path) -> None:
    text = valid_config.read_text(encoding="utf-8")
    text += "\n[reference]\n\"TICKET\" = '^TICKET-[0-9]+$'\n"
    config = load_config(write(tmp_path, text))
    assert any(spec.mark == "REFERENCE-TICKET" for spec in config.reference)


def test_reference_invalid_pattern(tmp_path: Path, valid_config: Path) -> None:
    text = valid_config.read_text(encoding="utf-8")
    text += "\n[reference]\n\"BAD\" = '['\n"
    with pytest.raises(ProgramError, match="invalid pattern"):
        load_config(write(tmp_path, text))


RULES = (
    CommitRule(path="**", types=("chore",)),
    CommitRule(path="src/**", types=("feat", "fix")),
    CommitRule(path="docs/**", types=("docs",)),
)


def test_last_match_wins() -> None:
    matcher = Matcher(RULES)
    rule = matcher.match("src/api/a.py")
    assert rule is not None
    assert rule.types == ("feat", "fix")


def test_catch_all_applies_when_nothing_else_matches() -> None:
    matcher = Matcher(RULES)
    rule = matcher.match("vendor/a.js")
    assert rule is not None
    assert rule.types == ("chore",)


def test_unmatched_path_returns_none() -> None:
    matcher = Matcher((CommitRule(path="src/**", types=("feat",)),))
    assert matcher.match("docs/a.md") is None


def test_later_rule_overrides_earlier_specific_rule() -> None:
    rules = (
        CommitRule(path="src/**", types=("feat",)),
        CommitRule(path="**", types=("chore",)),
    )
    matcher = Matcher(rules)
    rule = matcher.match("src/a.py")
    assert rule is not None
    assert rule.types == ("chore",)


def test_negated_pattern_is_rejected() -> None:
    with pytest.raises(ProgramError, match="negated"):
        Matcher((CommitRule(path="!src/**", types=("feat",)),))


def test_repository_config_loads() -> None:
    config = load_config(Path("config/lint-commit.toml"))
    assert "feat" in config.commit_type
    assert any(rule.path == "src/**" for rule in config.commit_rule)


def test_find_config_at_root(tmp_path: Path) -> None:
    path = tmp_path / "lint-commit.toml"
    path.write_text(MINIMAL, encoding="utf-8")
    assert find_config(tmp_path) == path


def test_find_config_under_config(tmp_path: Path) -> None:
    directory = tmp_path / "config"
    directory.mkdir()
    path = directory / "lint-commit.toml"
    path.write_text(MINIMAL, encoding="utf-8")
    assert find_config(tmp_path) == path


def test_find_config_prefers_root(tmp_path: Path) -> None:
    root = tmp_path / "lint-commit.toml"
    root.write_text(MINIMAL, encoding="utf-8")
    directory = tmp_path / "config"
    directory.mkdir()
    (directory / "lint-commit.toml").write_text(MINIMAL, encoding="utf-8")
    assert find_config(tmp_path) == root


def test_find_config_missing(tmp_path: Path) -> None:
    assert find_config(tmp_path) is None
