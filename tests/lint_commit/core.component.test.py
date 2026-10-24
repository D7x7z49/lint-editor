# @path[tests/lint_commit/core.component.test.py]

import re

from lint_commit.core import check
from lint_commit.schema import (
    CommitConfig,
    CommitRule,
    Reason,
    ReferenceSpec,
)

REFERENCE = (
    ReferenceSpec(mark="REFERENCE-LINK", pattern=re.compile(r"^https?://\S+$")),
)

CONFIG = CommitConfig(
    commit_type={
        "feat": "a feature",
        "fix": "a bug fix",
        "docs": "documentation",
        "chore": "maintenance",
    },
    commit_rule=(
        CommitRule(path="**", types=("chore",)),
        CommitRule(path="src/**", types=("feat", "fix")),
        CommitRule(path="docs/**", types=("docs",)),
    ),
    reference=REFERENCE,
)

DESCRIPTION = "add a parser for the nested arrays"
BODY = "\n".join(f"- entry {index}" for index in range(5))
PASSING = f"feat(api): {DESCRIPTION}\n\n{BODY}\n"
LONG_BREAKING = "this change drops the old route handler"


def test_valid_commit_passes() -> None:
    verdict = check(PASSING, CONFIG, ["src/api/a.py"])
    assert verdict.passed


def test_syntax_error() -> None:
    verdict = check("nope\n", CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.SYNTAX


def test_description_below_the_minimum() -> None:
    text = f"feat(api): {'a' * 31}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.SYNTAX


def test_description_at_the_minimum() -> None:
    text = f"feat(api): {'a' * 32}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.passed


def test_description_above_the_maximum() -> None:
    text = f"feat(api): {'a' * 73}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.SYNTAX


def test_body_below_the_minimum() -> None:
    text = f"feat(api): {DESCRIPTION}\n\n- one\n- two\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.BODY_COUNT


def test_body_above_the_maximum() -> None:
    body = "\n".join(f"- entry {index}" for index in range(10))
    text = f"feat(api): {DESCRIPTION}\n\n{body}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.BODY_COUNT


def test_uncovered_path() -> None:
    config = CommitConfig(
        commit_type={"feat": "a feature"},
        commit_rule=(CommitRule(path="src/**", types=("feat",)),),
        reference=(),
    )
    verdict = check(PASSING, config, ["src/api/a.py", "docs/b.md"])
    assert verdict.reason == Reason.UNCOVERED
    assert "docs/b.md" in verdict.detail


def test_empty_intersection_means_split() -> None:
    verdict = check(PASSING, CONFIG, ["src/api/a.py", "docs/b.md"])
    assert verdict.reason == Reason.SPLIT
    assert "src/api/a.py" in verdict.detail
    assert "docs/b.md" in verdict.detail


def test_type_outside_the_allowed_set() -> None:
    text = f"chore(api): {DESCRIPTION}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.TYPE
    assert "feat" in verdict.detail


def test_scope_mismatch() -> None:
    text = f"feat: {DESCRIPTION}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.SCOPE
    assert "api" in verdict.detail


def test_scope_must_be_empty_at_the_root() -> None:
    config = CommitConfig(
        commit_type={"chore": "maintenance"},
        commit_rule=(CommitRule(path="**", types=("chore",)),),
        reference=(),
    )
    text = f"chore(src): {DESCRIPTION}\n"
    verdict = check(text, config, ["a.py"])
    assert verdict.reason == Reason.SCOPE


def test_breaking_marker_and_footer_must_agree() -> None:
    text = f"feat(api)!: {DESCRIPTION}\n\n{BODY}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER


def test_breaking_footer_without_marker() -> None:
    text = f"feat(api): {DESCRIPTION}\n\n{BODY}\n\nBREAKING-CHANGE: {LONG_BREAKING}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER


def test_breaking_footer_with_marker_passes() -> None:
    text = f"feat(api)!: {DESCRIPTION}\n\n{BODY}\n\nBREAKING-CHANGE: {LONG_BREAKING}\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.passed


def test_breaking_footer_must_be_unique() -> None:
    text = (
        f"feat(api)!: {DESCRIPTION}\n\n{BODY}\n\n"
        f"BREAKING-CHANGE: {LONG_BREAKING}\n"
        f"BREAKING-CHANGE: {LONG_BREAKING}\n"
    )
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER


def test_breaking_footer_below_the_minimum() -> None:
    text = f"feat(api)!: {DESCRIPTION}\n\n{BODY}\n\nBREAKING-CHANGE: short\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER


def test_unknown_footer_mark() -> None:
    text = f"feat(api): {DESCRIPTION}\n\n{BODY}\n\nREFERENCE-NOPE: value\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER
    assert "REFERENCE-NOPE" in verdict.detail


def test_reference_value_must_match_its_pattern() -> None:
    text = f"feat(api): {DESCRIPTION}\n\n{BODY}\n\nREFERENCE-LINK: not a url\n"
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.reason == Reason.FOOTER


def test_reference_value_matching_its_pattern_passes() -> None:
    text = (
        f"feat(api): {DESCRIPTION}\n\n{BODY}\n\n"
        "REFERENCE-LINK: https://example.com/spec\n"
    )
    verdict = check(text, CONFIG, ["src/api/a.py"])
    assert verdict.passed


def test_empty_path_list_only_checks_format() -> None:
    text = f"feat: {DESCRIPTION}\n"
    verdict = check(text, CONFIG, [])
    assert verdict.passed


def test_empty_path_list_still_checks_body_count() -> None:
    text = f"feat: {DESCRIPTION}\n\n- one\n"
    verdict = check(text, CONFIG, [])
    assert verdict.reason == Reason.BODY_COUNT
