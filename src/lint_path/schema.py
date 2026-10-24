# @path[src/lint_path/schema.py]
# ==============================================================================
# types shared by parsing, locating, and judging

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .matching import PathPattern
    from .projection import PathProjection

# ==============================================================================
# ERRORS
# ==============================================================================


class ProgramError(Exception):
    # a failure of the tool itself, not a verdict about a path
    pass


class PathContractError(ValueError):
    # the contract file does not follow the grammar
    pass


# ==============================================================================
# RECORDS
# ==============================================================================


@dataclass(frozen=True)
class PathRule:
    name: str
    pattern: PathPattern
    mode: str
    source: str | None = None
    projection: PathProjection | None = None


@dataclass(frozen=True)
class PathContract:
    directory: str
    rules: tuple[PathRule, ...]
    header: dict[str, str]
    imports: dict[str, str]


@dataclass(frozen=True)
class PathVerdict:
    allowed: bool
    reason: str | None = None
    rule: PathRule | None = None


@dataclass(frozen=True)
class PathFinding:
    path: str | None
    domain: str | None
    rule: PathRule | None
    reason: str
