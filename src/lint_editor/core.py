# @path[src/lint_editor/core.py]

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

from .attributes import declared_non_text
from .constants import BINARY_SNIFF_BYTES, MESSAGE_NOT_DECLARED
from .editorconfig import check_text
from .errors import ProgramError


class Finding(NamedTuple):
    path: str
    message: str


def is_binary(path: Path) -> bool:
    # git treats a NUL byte in the first 8000 bytes as binary
    with path.open("rb") as handle:
        return b"\0" in handle.read(BINARY_SNIFF_BYTES)


def check_paths(paths: Sequence[str]) -> list[Finding]:
    # split the inputs by kind, then apply the policy for each kind
    text_paths: list[Path] = []
    non_text_paths: list[Path] = []

    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        try:
            binary = is_binary(path)
        except OSError as error:
            message = f"{raw}: {error}"
            raise ProgramError(message) from error
        if binary:
            non_text_paths.append(path)
        else:
            text_paths.append(path)

    declared = declared_non_text(non_text_paths)
    findings: list[Finding] = [
        Finding(str(path), MESSAGE_NOT_DECLARED)
        for path in non_text_paths
        if path not in declared
    ]

    for path in text_paths:
        try:
            messages = check_text(path)
        except OSError as error:
            message = f"{path}: {error}"
            raise ProgramError(message) from error
        findings.extend(Finding(str(path), message) for message in messages)

    return findings
