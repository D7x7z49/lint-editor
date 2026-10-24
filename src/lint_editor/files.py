# @path[src/lint_editor/files.py]
# ==============================================================================
# classify a path as text or non-text and read its git attributes

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .constants import ATTRIBUTE_COMMAND, BINARY_SNIFF_BYTES, NON_TEXT_VALUES, msg
from .schema import ProgramError

# ==============================================================================
# CLASSIFY
# ==============================================================================


def is_binary(path: Path) -> bool:
    # git treats a NUL byte in the first 8000 bytes as binary
    with path.open("rb") as handle:
        return b"\0" in handle.read(BINARY_SNIFF_BYTES)


# ==============================================================================
# ATTRIBUTES
# ==============================================================================


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
        raise ProgramError(msg("git.run.failed", reason=error)) from error

    if result.returncode != 0:
        raise ProgramError(msg("git.attributes.failed", code=result.returncode))

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
