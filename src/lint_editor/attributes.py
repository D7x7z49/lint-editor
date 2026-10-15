# @path[src/lint_editor/attributes.py]

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .errors import ProgramError

# ask git to resolve the two attributes that mark a path as non-text
ATTRIBUTE_COMMAND = ("git", "check-attr", "--stdin", "-z", "binary", "text")
NON_TEXT_VALUES = {b"binary": b"set", b"text": b"unset"}


def declared_non_text(paths: Sequence[Path]) -> set[Path]:
    # return the paths that .gitattributes explicitly declares non-text
    if not paths:
        return set()

    payload = b"".join(os.fsencode(path) + b"\0" for path in paths)
    try:
        result = subprocess.run(  # noqa: S603 (fixed argument list)
            ATTRIBUTE_COMMAND,
            input=payload,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        message = f"cannot run git: {error}"
        raise ProgramError(message) from error

    if result.returncode != 0:
        message = f"git check-attr failed with exit code {result.returncode}"
        raise ProgramError(message)

    return _parse_declared(result.stdout)


def _parse_declared(output: bytes) -> set[Path]:
    # git prints a path, attribute, and value for every requested attribute
    fields = output.split(b"\0")
    paths: set[Path] = set()
    for raw_path, attribute, value in zip(
        fields[0::3], fields[1::3], fields[2::3], strict=False
    ):
        if NON_TEXT_VALUES.get(attribute) == value:
            paths.add(Path(os.fsdecode(raw_path)))
    return paths
