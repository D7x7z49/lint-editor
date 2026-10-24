# @path[src/lint_path/matching.py]
# ==============================================================================
# parse a path pattern into nodes and match it against a path

from __future__ import annotations

import re
from dataclasses import dataclass

PATTERN_PREFIX = "pattern must start with /"
TAIL_PREFIX = "unexpected text after group"
QUANTIFIER_OPEN = "unclosed quantifier"

# ==============================================================================
# NODES
# ==============================================================================


@dataclass(frozen=True)
class PathLiteral:
    # one segment, matched by a compiled expression
    regex: re.Pattern[str]


@dataclass(frozen=True)
class PathStar:
    # one non empty segment
    pass


@dataclass(frozen=True)
class PathGlobstar:
    # zero or more segments
    pass


@dataclass(frozen=True)
class PathGroup:
    # a nested segment sequence
    nodes: tuple[PathNode, ...]


@dataclass(frozen=True)
class PathRepeat:
    # a node repeated between minimum and maximum times
    node: PathNode
    minimum: int
    maximum: int | None


PathNode = PathLiteral | PathStar | PathGlobstar | PathGroup | PathRepeat
PathSegment = PathLiteral | PathStar | PathGlobstar

# ==============================================================================
# PATTERN
# ==============================================================================


@dataclass(frozen=True)
class PathPattern:
    nodes: tuple[PathNode, ...]
    is_dir: bool


def parse_pattern(text: str) -> PathPattern:
    if not text.startswith("/"):
        raise ValueError(PATTERN_PREFIX)

    is_dir = text.endswith("/")
    body = text[1:-1] if is_dir else text[1:]
    if not body:
        return PathPattern((), is_dir)

    return PathPattern(parse_nodes(body), is_dir)


def parse_nodes(body: str) -> tuple[PathNode, ...]:
    parts = split_segments(body)
    return tuple(parse_segment(part) for part in parts if part)


def split_segments(body: str) -> list[str]:
    # split on / but keep a group that contains / in one piece
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0

    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)

        if char == "/" and depth == 0:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)

    parts.append("".join(buffer))
    return parts


def parse_segment(part: str) -> PathNode:
    if part == "**":
        return PathGlobstar()
    if part == "*":
        return PathStar()

    if part.startswith("("):
        close = matching_paren(part)
        if close is not None and "/" in part[1:close]:
            node: PathNode = PathGroup(parse_nodes(part[1:close]))
            return apply_quantifier(node, part[close + 1 :])

    return PathLiteral(re.compile(to_regex(part)))


def matching_paren(part: str) -> int | None:
    depth = 0
    for index, char in enumerate(part):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def apply_quantifier(node: PathNode, tail: str) -> PathNode:
    if not tail:
        return node
    if not tail.startswith("{"):
        raise ValueError(TAIL_PREFIX + " " + tail)

    close = tail.find("}")
    if close == -1:
        raise ValueError(QUANTIFIER_OPEN)

    body = tail[1:close]
    if "," not in body:
        count = int(body)
        return PathRepeat(node, count, count)

    minimum, maximum = body.split(",", 1)
    low = int(minimum)
    high = int(maximum) if maximum else None
    return PathRepeat(node, low, high)


# ==============================================================================
# REGEX
# ==============================================================================


def to_regex(part: str) -> str:
    # convert one segment into an anchored-free regular expression
    result: list[str] = []
    index = 0

    while index < len(part):
        char = part[index]

        if char == "\\" and index + 1 < len(part):
            result.append(re.escape(part[index + 1]))
            index += 2
            continue

        if char == "[":
            text, index = class_regex(part, index)
        elif char == "{":
            text, index = alternation_regex(part, index)
        else:
            text = char_regex(char)

        result.append(text)
        index += 1

    return "".join(result)


def char_regex(char: str) -> str:
    if char == ".":
        return "[^/]"
    if char == "*":
        return "[^/]*"
    if char in "()|":
        return char
    return re.escape(char)


def class_regex(part: str, index: int) -> tuple[str, int]:
    close = part.find("]", index + 1)
    if close == -1:
        return re.escape("["), index

    body = part[index + 1 : close]
    if body.startswith("!"):
        body = "^" + body[1:]
    return "[" + body + "]", close


def alternation_regex(part: str, index: int) -> tuple[str, int]:
    close = part.find("}", index + 1)
    if close == -1:
        return re.escape("{"), index

    body = part[index + 1 : close]
    choices = "|".join(re.escape(item) for item in body.split(","))
    return "(" + choices + ")", close


# ==============================================================================
# MATCH
# ==============================================================================


def match_pattern(
    pattern: PathPattern, segments: tuple[str, ...], *, is_dir: bool
) -> bool:
    if pattern.is_dir != is_dir:
        return False
    return len(segments) in match_positions(pattern.nodes, segments, 0)


def match_positions(
    nodes: tuple[PathNode, ...], segments: tuple[str, ...], start: int
) -> set[int]:
    # every segment position reachable after matching the node sequence
    if not nodes:
        return {start}

    node = nodes[0]
    rest = nodes[1:]
    result: set[int] = set()

    for end in node_end_positions(node, segments, start):
        result |= match_positions(rest, segments, end)

    return result


def node_end_positions(
    node: PathNode, segments: tuple[str, ...], start: int
) -> set[int]:
    if isinstance(node, PathGlobstar):
        return set(range(start, len(segments) + 1))

    if isinstance(node, PathStar):
        return {start + 1} if start < len(segments) else set()

    if isinstance(node, PathLiteral):
        if start < len(segments) and node.regex.fullmatch(segments[start]):
            return {start + 1}
        return set()

    if isinstance(node, PathGroup):
        return match_positions(node.nodes, segments, start)

    return repeat_end_positions(node, segments, start)


def repeat_end_positions(
    node: PathRepeat, segments: tuple[str, ...], start: int
) -> set[int]:
    limit = node.maximum if node.maximum is not None else len(segments) + 1
    result: set[int] = set()
    frontier = {start}
    count = 0

    while frontier and count <= limit:
        if count >= node.minimum:
            result |= frontier

        next_frontier: set[int] = set()
        for position in frontier:
            next_frontier |= node_end_positions(node.node, segments, position)

        frontier = next_frontier
        count += 1

    return result
