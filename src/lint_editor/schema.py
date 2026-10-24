# @path[src/lint_editor/schema.py]
# ==============================================================================
# types shared by checking and reporting

from collections.abc import Callable
from typing import NamedTuple

# ==============================================================================
# ERRORS
# ==============================================================================


class ProgramError(Exception):
    # a failure of the tool itself, not a finding about a file
    pass


# ==============================================================================
# RECORDS
# ==============================================================================


class Finding(NamedTuple):
    path: str
    message: str


# ==============================================================================
# VALIDATORS
# ==============================================================================

Validator = Callable[[bytes, str], str | None]
