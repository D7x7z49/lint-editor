# @path[src/lint_commit/message.py]
# ==============================================================================
# parse a commit message into its head, body, and footer sections

from .constants import msg
from .schema import HEADER, CommitHead, CommitMessage, MessageError

# ==============================================================================
# SECTIONS
# ==============================================================================


def parse_head(line: str) -> CommitHead:
    match = HEADER.fullmatch(line)
    if match is None:
        raise MessageError(msg("message.head.syntax"))

    return CommitHead(
        type=match.group("type"),
        scope=match.group("scope"),
        breaking=match.group("breaking") is not None,
        description=match.group("description"),
    )


def parse_body(lines: list[str]) -> tuple[tuple[str, ...], list[str]]:
    items: list[str] = []
    while lines and lines[0].startswith("- "):
        items.append(lines[0][2:])
        lines = lines[1:]
    return tuple(items), lines


def parse_footers(lines: list[str]) -> tuple[tuple[tuple[str, str], ...], list[str]]:
    footers: list[tuple[str, str]] = []
    while lines:
        mark, separator, value = lines[0].partition(": ")
        if not separator:
            raise MessageError(msg("message.foot.syntax", line=lines[0]))
        footers.append((mark, value))
        lines = lines[1:]
    return tuple(footers), lines


def split_lines(text: str) -> list[str]:
    # one trailing newline ends the last line rather than adding an empty one
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.removesuffix("\r") for line in lines]


# ==============================================================================
# MESSAGE
# ==============================================================================


def parse_message(text: str) -> CommitMessage:
    lines = split_lines(text)
    if not lines:
        raise MessageError(msg("message.text.empty"))

    head = parse_head(lines[0])
    rest = lines[1:]

    body: tuple[str, ...] = ()
    footers: tuple[tuple[str, str], ...] = ()

    if rest:
        if rest[0] != "":
            raise MessageError(msg("message.head.blank"))
        rest = rest[1:]

        body, rest = parse_body(rest)

        if rest:
            if body:
                if rest[0] != "":
                    raise MessageError(msg("message.body.blank"))
                rest = rest[1:]
            footers, rest = parse_footers(rest)

        if rest:
            raise MessageError(msg("message.tail.content"))

    return CommitMessage(head=head, body=body, footers=footers)
