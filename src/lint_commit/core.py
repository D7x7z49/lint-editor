# @path[src/lint_commit/core.py]
# ==============================================================================
# judge a parsed message and the staged paths into one verdict

from collections.abc import Sequence
from pathlib import PurePosixPath

from .constants import (
    BODY_ITEMS,
    BREAKING_LENGTH,
    BREAKING_MARK,
    DESCRIPTION_LENGTH,
    msg,
)
from .message import parse_message
from .rules import Matcher
from .schema import (
    IDENTIFIER,
    CommitConfig,
    CommitMessage,
    CommitVerdict,
    MessageError,
    Reason,
)

# ==============================================================================
# SCOPE
# ==============================================================================


def common_prefix(first: tuple[str, ...], second: tuple[str, ...]) -> tuple[str, ...]:
    length = 0
    for left, right in zip(first, second, strict=False):
        if left != right:
            break
        length += 1
    return first[:length]


def derive_scope(paths: Sequence[str]) -> str | None:
    # the scope is the name of the deepest directory shared by every path
    if not paths:
        return None

    parents = [PurePosixPath(path).parent.parts for path in paths]
    common = parents[0]
    for parts in parents[1:]:
        common = common_prefix(common, parts)

    if not common:
        return None
    return common[-1]


# ==============================================================================
# DISPLAY
# ==============================================================================


def show(value: str | None) -> str:
    return "none" if value is None else f"[{value}]"


def show_marker(*, value: bool) -> str:
    return "present" if value else "absent"


def describe_split(selected: Sequence[tuple[str, set[str]]]) -> str:
    lines = [f"  [{path}] {', '.join(sorted(types))}" for path, types in selected]
    return "\n".join(lines)


# ==============================================================================
# FOOTER
# ==============================================================================


def check_footer(message: CommitMessage, config: CommitConfig) -> CommitVerdict | None:
    breaking = [value for mark, value in message.footers if mark == BREAKING_MARK]
    if len(breaking) > 1:
        return CommitVerdict(Reason.FOOTER, msg("verdict.foot.breaking"))

    expected = bool(breaking)
    if message.head.breaking != expected:
        detail = msg(
            "verdict.foot.marker",
            actual=show_marker(value=message.head.breaking),
            expected=show_marker(value=expected),
        )
        return CommitVerdict(Reason.FOOTER, detail)

    if breaking:
        low, high = BREAKING_LENGTH
        count = len(breaking[0])
        if not low <= count <= high:
            detail = msg(
                "verdict.foot.length",
                mark=BREAKING_MARK,
                count=count,
                low=low,
                high=high,
            )
            return CommitVerdict(Reason.FOOTER, detail)

    specs = {spec.mark: spec for spec in config.reference}
    for mark, value in message.footers:
        if mark == BREAKING_MARK:
            continue
        spec = specs.get(mark)
        if spec is None:
            allowed = ", ".join(sorted(specs))
            detail = msg("verdict.foot.mark", mark=mark, allowed=allowed)
            return CommitVerdict(Reason.FOOTER, detail)
        if spec.pattern.fullmatch(value) is None:
            return CommitVerdict(Reason.FOOTER, msg("verdict.foot.value", mark=mark))
    return None


# ==============================================================================
# PATHS
# ==============================================================================


def resolve_paths(
    paths: Sequence[str], config: CommitConfig
) -> list[tuple[str, set[str]]] | CommitVerdict:
    matcher = Matcher(config.commit_rule)
    selected: list[tuple[str, set[str]]] = []
    for path in paths:
        rule = matcher.match(path)
        if rule is None:
            return CommitVerdict(
                Reason.UNCOVERED, msg("verdict.path.uncovered", path=path)
            )
        selected.append((path, set(rule.types)))
    return selected


def check_allowed(
    message: CommitMessage, selected: Sequence[tuple[str, set[str]]]
) -> CommitVerdict | None:
    allowed = set.intersection(*(types for _, types in selected))
    if not allowed:
        detail = msg("verdict.path.split") + "\n" + describe_split(selected)
        return CommitVerdict(Reason.SPLIT, detail)
    if message.head.type not in allowed:
        names = ", ".join(sorted(allowed))
        detail = msg("verdict.type.mismatch", value=message.head.type, allowed=names)
        return CommitVerdict(Reason.TYPE, detail)
    return None


def check_scope(message: CommitMessage, paths: Sequence[str]) -> CommitVerdict | None:
    scope = derive_scope(paths)
    if scope is not None and IDENTIFIER.fullmatch(scope) is None:
        return CommitVerdict(Reason.SCOPE, msg("verdict.scope.invalid", scope=scope))
    if message.head.scope != scope:
        detail = msg(
            "verdict.scope.mismatch",
            actual=show(message.head.scope),
            expected=show(scope),
        )
        return CommitVerdict(Reason.SCOPE, detail)
    return None


# ==============================================================================
# ENTRY
# ==============================================================================


def check_shape(message: CommitMessage) -> CommitVerdict | None:
    low, high = DESCRIPTION_LENGTH
    count = len(message.head.description)
    if not low <= count <= high:
        detail = msg("verdict.description.length", count=count, low=low, high=high)
        return CommitVerdict(Reason.SYNTAX, detail)

    low, high = BODY_ITEMS
    count = len(message.body)
    if message.body and not low <= count <= high:
        detail = msg("verdict.body.count", count=count, low=low, high=high)
        return CommitVerdict(Reason.BODY_COUNT, detail)
    return None


def check(
    message_text: str, config: CommitConfig, paths: Sequence[str]
) -> CommitVerdict:
    try:
        message = parse_message(message_text)
    except MessageError as error:
        return CommitVerdict(Reason.SYNTAX, msg("verdict.syntax.invalid", reason=error))

    shape = check_shape(message)
    if shape is not None:
        return shape

    footer = check_footer(message, config)
    if footer is not None:
        return footer

    if paths:
        selected = resolve_paths(paths, config)
        if isinstance(selected, CommitVerdict):
            return selected
        for verdict in (check_allowed(message, selected), check_scope(message, paths)):
            if verdict is not None:
                return verdict

    return CommitVerdict(None, "")
