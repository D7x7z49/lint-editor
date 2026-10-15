# @path[src/lint_editor/editorconfig.py]

from collections.abc import Callable
from pathlib import Path

from editorconfig import EditorConfigError, get_properties

from .constants import (
    BOOLEAN_TRUE,
    INDENT_STYLES,
    MESSAGE_CHARSET,
    MESSAGE_END_OF_LINE,
    MESSAGE_FINAL_NEWLINE,
    MESSAGE_INDENT_STYLE,
    MESSAGE_LINE_LENGTH,
    MESSAGE_NO_RULES,
    MESSAGE_TRAILING_WHITESPACE,
)
from .errors import ProgramError

Validator = Callable[[bytes, str], str | None]


def check_text(path: Path) -> list[str]:
    # return one message for each violated editorconfig property
    try:
        properties = get_properties(str(path.resolve()))
    except EditorConfigError as error:
        detail = f"{path}: {error}"
        raise ProgramError(detail) from error

    if not properties:
        detail = f"{path}: {MESSAGE_NO_RULES}"
        raise ProgramError(detail)

    with path.open("rb") as handle:
        data = handle.read()

    messages: list[str] = []
    for name, value in properties.items():
        message = validate_property(name, data, value)
        if message is not None:
            messages.append(message)
    return messages


def validate_property(name: str, data: bytes, value: str) -> str | None:
    # return None when the property is unknown or satisfied
    validator = VALIDATORS.get(name)
    if validator is None:
        return None
    return validator(data, value)


def _decodes(data: bytes, encoding: str) -> bool:
    try:
        data.decode(encoding)
    except UnicodeDecodeError:
        return False
    return True


def _check_charset(data: bytes, value: str) -> str | None:
    if value == "utf-8":
        ok = not data.startswith(b"\xef\xbb\xbf") and _decodes(data, "utf-8")
    elif value == "utf-8-bom":
        ok = data.startswith(b"\xef\xbb\xbf") and _decodes(data, "utf-8")
    elif value in ("utf-16be", "utf-16le"):
        ok = _decodes(data, value)
    else:
        return None
    if ok:
        return None
    return MESSAGE_CHARSET.format(value=value)


def _check_end_of_line(data: bytes, value: str) -> str | None:
    if value == "lf":
        broken = b"\r" in data
    elif value == "cr":
        broken = b"\n" in data
    elif value == "crlf":
        rest = data.replace(b"\r\n", b"")
        broken = b"\r" in rest or b"\n" in rest
    else:
        return None
    if not broken:
        return None
    return MESSAGE_END_OF_LINE.format(value=value)


def _check_insert_final_newline(data: bytes, value: str) -> str | None:
    if value != BOOLEAN_TRUE:
        return None
    if data and not data.endswith(b"\n"):
        return MESSAGE_FINAL_NEWLINE
    return None


def _check_trim_trailing_whitespace(data: bytes, value: str) -> str | None:
    if value != BOOLEAN_TRUE:
        return None
    for number, line in enumerate(data.split(b"\n"), start=1):
        if line.rstrip(b"\r").endswith((b" ", b"\t")):
            return MESSAGE_TRAILING_WHITESPACE.format(line=number)
    return None


def _check_indent_style(data: bytes, value: str) -> str | None:
    if value not in INDENT_STYLES:
        return None
    for number, line in enumerate(data.split(b"\n"), start=1):
        indent = line[: len(line) - len(line.lstrip(b" \t"))]
        if value == "space" and b"\t" in indent:
            return MESSAGE_INDENT_STYLE.format(line=number, value=value)
        if value == "tab" and b" " in indent:
            return MESSAGE_INDENT_STYLE.format(line=number, value=value)
    return None


def _check_max_line_length(data: bytes, value: str) -> str | None:
    if value == "off":
        return None
    try:
        limit = int(value)
    except ValueError:
        return None
    if limit <= 0:
        return None
    for number, line in enumerate(data.split(b"\n"), start=1):
        length = len(line.rstrip(b"\r").decode("utf-8", errors="replace"))
        if length > limit:
            return MESSAGE_LINE_LENGTH.format(line=number, value=value)
    return None


VALIDATORS: dict[str, Validator] = {
    "charset": _check_charset,
    "end_of_line": _check_end_of_line,
    "indent_style": _check_indent_style,
    "insert_final_newline": _check_insert_final_newline,
    "max_line_length": _check_max_line_length,
    "trim_trailing_whitespace": _check_trim_trailing_whitespace,
}
