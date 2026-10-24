# @path[src/lint_commit/rules.py]
# ==============================================================================
# load the config file and resolve a path to its last matching rule

import re
import tomllib
from pathlib import Path

from pathspec.patterns.gitignore import GitIgnorePatternError
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern

from .constants import REFERENCE_FOOTERS, REFERENCE_PREFIX, TYPES, msg
from .schema import CommitConfig, CommitRule, ProgramError, ReferenceSpec

# ==============================================================================
# LOADING
# ==============================================================================


def read_commit_type(data: dict[str, object]) -> dict[str, str]:
    table = data.get("types")
    if not isinstance(table, dict):
        raise ProgramError(msg("config.table.missing", table="types"))
    if not table:
        raise ProgramError(msg("config.table.empty", table="types"))

    result: dict[str, str] = {}
    for name, description in table.items():
        if name not in TYPES:
            allowed = ", ".join(TYPES)
            raise ProgramError(msg("config.type.unknown", name=name, allowed=allowed))
        if not isinstance(description, str):
            raise ProgramError(msg("config.type.value", name=name))
        result[name] = description
    return result


def read_commit_rule(
    data: dict[str, object], commit_type: dict[str, str]
) -> tuple[CommitRule, ...]:
    table = data.get("rules")
    if not isinstance(table, dict):
        raise ProgramError(msg("config.table.missing", table="rules"))
    if not table:
        raise ProgramError(msg("config.table.empty", table="rules"))

    result: list[CommitRule] = []
    for pattern, allowed in table.items():
        if not isinstance(allowed, list) or not allowed:
            raise ProgramError(msg("config.rule.path", pattern=pattern))
        for name in allowed:
            if not isinstance(name, str) or name not in commit_type:
                raise ProgramError(msg("config.rule.type", pattern=pattern, name=name))
        result.append(CommitRule(path=pattern, types=tuple(allowed)))
    return tuple(result)


def read_reference(data: dict[str, object]) -> tuple[ReferenceSpec, ...]:
    # built in marks are merged with config entries, a config entry wins
    table = data.get("reference", {})
    if not isinstance(table, dict):
        raise ProgramError(msg("config.table.missing", table="reference"))

    patterns = dict(REFERENCE_FOOTERS)
    for name, pattern in table.items():
        if not isinstance(pattern, str):
            raise ProgramError(
                msg("config.reference.pattern", name=name, reason="not a string")
            )
        patterns[name] = pattern

    result: list[ReferenceSpec] = []
    for name, pattern in patterns.items():
        try:
            compiled = re.compile(pattern)
        except re.error as error:
            raise ProgramError(
                msg("config.reference.pattern", name=name, reason=error)
            ) from error
        result.append(ReferenceSpec(mark=REFERENCE_PREFIX + name, pattern=compiled))
    return tuple(result)


def load_config(path: Path) -> CommitConfig:
    if not path.is_file():
        raise ProgramError(msg("config.file.missing", path=path))

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ProgramError(
            msg("config.file.invalid", path=path, reason=error)
        ) from error

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ProgramError(
            msg("config.file.invalid", path=path, reason=error)
        ) from error

    unknown = set(data) - {"types", "rules", "reference"}
    if unknown:
        name = sorted(unknown)[0]
        raise ProgramError(msg("config.key.unexpected", name=name))

    commit_type = read_commit_type(data)
    commit_rule = read_commit_rule(data, commit_type)
    reference = read_reference(data)
    return CommitConfig(
        commit_type=commit_type, commit_rule=commit_rule, reference=reference
    )


# ==============================================================================
# MATCHING
# ==============================================================================


class Matcher:
    # resolve a path to the last rule that matches it, following file order
    def __init__(self, commit_rule: tuple[CommitRule, ...]) -> None:
        self._entries: list[tuple[GitIgnoreBasicPattern, CommitRule]] = []
        for rule in commit_rule:
            if rule.path.startswith("!"):
                raise ProgramError(msg("pattern.glob.negated", pattern=rule.path))
            try:
                pattern = GitIgnoreBasicPattern(rule.path)
            except GitIgnorePatternError as error:
                raise ProgramError(
                    msg("pattern.glob.invalid", pattern=rule.path, reason=error)
                ) from error
            self._entries.append((pattern, rule))

    def match(self, path: str) -> CommitRule | None:
        hit: CommitRule | None = None
        for pattern, rule in self._entries:
            if pattern.match_file(path) is not None:
                hit = rule
        return hit
