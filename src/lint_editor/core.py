# @path[src/lint_editor/core.py]
# ==============================================================================
# check every supplied path and collect one finding per violation

from collections.abc import Sequence
from pathlib import Path

from .constants import msg
from .editorconfig import check_text
from .files import declared_non_text, is_binary
from .schema import Finding, ProgramError

# ==============================================================================
# PIPELINE
# ==============================================================================


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
            raise ProgramError(msg("path.failed", path=raw, reason=error)) from error
        if binary:
            non_text_paths.append(path)
        else:
            text_paths.append(path)

    declared = declared_non_text(non_text_paths)
    findings: list[Finding] = [
        Finding(str(path), msg("check.not_declared"))
        for path in non_text_paths
        if path not in declared
    ]

    for path in text_paths:
        try:
            messages = check_text(path)
        except OSError as error:
            raise ProgramError(msg("path.failed", path=path, reason=error)) from error
        findings.extend(Finding(str(path), message) for message in messages)

    return findings
