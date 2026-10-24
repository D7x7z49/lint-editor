# @path[src/lint_path/projection.py]
# ==============================================================================
# parse and apply a projection chain

import re
from dataclasses import dataclass

PROJECTION_PREFIX = "projection must start with @"
SUBSTITUTION_FORMAT = "expected s|pattern|replacement|, got"
SUBSTITUTION_PREFIX = 2


@dataclass(frozen=True)
class PathSubstitution:
    pattern: re.Pattern[str]
    replacement: str


@dataclass(frozen=True)
class PathProjection:
    source: str | None
    rule: str
    mapping: tuple[PathSubstitution, ...]


def parse_projection(value: str, separator: str = "|") -> PathProjection:
    parts = [part.strip() for part in value.split(">>")]
    head = parts[0]

    if not head.startswith("@"):
        raise ValueError(PROJECTION_PREFIX)

    if ":" in head:
        source, rule = head[1:].split(":", 1)
    else:
        source, rule = None, head[1:]

    mapping = tuple(parse_substitution(part, separator) for part in parts[1:] if part)
    return PathProjection(source=source, rule=rule, mapping=mapping)


def parse_substitution(text: str, separator: str = "|") -> PathSubstitution:
    if len(text) < SUBSTITUTION_PREFIX or text[0] != "s" or text[1] != separator:
        raise ValueError(SUBSTITUTION_FORMAT + " " + text)

    pattern, rest = split_unescaped(text[2:], separator)
    replacement, tail = split_unescaped(rest, separator)
    if tail:
        raise ValueError(SUBSTITUTION_FORMAT + " " + text)

    return PathSubstitution(re.compile(pattern), replacement)


def split_unescaped(text: str, separator: str) -> tuple[str, str]:
    index = 0
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == separator:
            return text[:index], text[index + 1 :]
        index += 1
    raise ValueError(SUBSTITUTION_FORMAT + " " + text)


def apply_mapping(projection: PathProjection, text: str) -> str:
    result = text
    for substitution in projection.mapping:
        result = substitution.pattern.sub(substitution.replacement, result)
    return result
