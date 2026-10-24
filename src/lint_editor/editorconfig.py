# @path[src/lint_editor/editorconfig.py]
# ==============================================================================
# check a text file against the editorconfig properties that apply to it

from pathlib import Path

from editorconfig import EditorConfigError, get_properties

from .constants import BOOLEAN_TRUE, INDENT_STYLES, msg
from .schema import ProgramError, Validator

# ==============================================================================
# POLICY
# ==============================================================================


def check_text(path: Path) -> list[str]:
    # return one message for each violated editorconfig property
    try:
        properties = get_properties(str(path.resolve()))
    except EditorConfigError as error:
        raise ProgramError(msg("path.failed", path=path, reason=error)) from error

    if not properties:
        raise ProgramError(msg("path.failed", path=path, reason=msg("check.no_rules")))

    with path.open("rb") as handle:
        data = handle.read()

    messages: list[str] = []
    for name, value in properties.items():
        message = validate_property(name, data, value)
        if message is not None:
            messages.append(message)
    return messages


# ==============================================================================
# DISPATCH
# ==============================================================================


def validate_property(name: str, data: bytes, value: str) -> str | None:
    # return None when the property is unknown or satisfied
    validator = VALIDATORS.get(name)
    if validator is None:
        return None
    return validator(data, value)


# ==============================================================================
# CHECKS
# ==============================================================================


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
    return msg("check.charset", value=value)


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
    return msg("check.end_of_line", value=value)


def _check_insert_final_newline(data: bytes, value: str) -> str | None:
    if value != BOOLEAN_TRUE:
        return None
    if data and not data.endswith(b"\n"):
        return msg("check.final_newline")
    return None


def _check_trim_trailing_whitespace(data: bytes, value: str) -> str | None:
    if value != BOOLEAN_TRUE:
        return None
    for number, line in enumerate(data.split(b"\n"), start=1):
        if line.rstrip(b"\r").endswith((b" ", b"\t")):
            return msg("check.trailing_whitespace", line=number)
    return None


def _check_indent_style(data: bytes, value: str) -> str | None:
    if value not in INDENT_STYLES:
        return None
    for number, line in enumerate(data.split(b"\n"), start=1):
        indent = line[: len(line) - len(line.lstrip(b" \t"))]
        if value == "space" and b"\t" in indent:
            return msg("check.indent_style", line=number, value=value)
        if value == "tab" and b" " in indent:
            return msg("check.indent_style", line=number, value=value)
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
            return msg("check.line_length", line=number, value=value)
    return None


# ==============================================================================
# REGISTRY
# ==============================================================================

VALIDATORS: dict[str, Validator] = {
    "charset": _check_charset,
    "end_of_line": _check_end_of_line,
    "indent_style": _check_indent_style,
    "insert_final_newline": _check_insert_final_newline,
    "max_line_length": _check_max_line_length,
    "trim_trailing_whitespace": _check_trim_trailing_whitespace,
}
