# @path[src/lint_commit/schema.py]
# ==============================================================================
# types shared by parsing, loading, and judging

import re
from dataclasses import dataclass
from enum import StrEnum

from .constants import TYPES

# ==============================================================================
# ERRORS
# ==============================================================================


class ProgramError(Exception):
    # a failure of the tool itself, not a verdict about a commit
    pass


class MessageError(ValueError):
    # the message does not follow the strict format
    pass


# ==============================================================================
# REASONS
# ==============================================================================


class Reason(StrEnum):
    SYNTAX = "syntax"
    BODY_COUNT = "body-count"
    FOOTER = "footer"
    UNCOVERED = "uncovered"
    SPLIT = "split"
    TYPE = "type"
    SCOPE = "scope"


# ==============================================================================
# PATTERNS
# ==============================================================================

# one identifier definition, shared by the header scope and the path scope
IDENTIFIER_PATTERN = r"[A-Za-z0-9._-]+"
IDENTIFIER = re.compile(IDENTIFIER_PATTERN)

HEADER = re.compile(
    rf"(?P<type>{'|'.join(TYPES)})"
    rf"(?:\((?P<scope>{IDENTIFIER_PATTERN})\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.*)"
)


# ==============================================================================
# RECORDS
# ==============================================================================


@dataclass(frozen=True)
class CommitHead:
    type: str
    scope: str | None
    breaking: bool
    description: str


@dataclass(frozen=True)
class CommitMessage:
    head: CommitHead
    body: tuple[str, ...]
    footers: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CommitRule:
    path: str
    types: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceSpec:
    mark: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class CommitConfig:
    commit_type: dict[str, str]
    commit_rule: tuple[CommitRule, ...]
    reference: tuple[ReferenceSpec, ...]


@dataclass(frozen=True)
class CommitVerdict:
    reason: Reason | None
    detail: str

    @property
    def passed(self) -> bool:
        return self.reason is None
