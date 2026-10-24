# @path[src/lint_editor/cli.py]
# ==============================================================================
# run the check and print one line per finding

import sys

from .constants import PROGRAM, STATUS_ERROR, STATUS_FINDINGS, STATUS_OK
from .core import check_paths
from .schema import ProgramError

# ==============================================================================
# COMMAND
# ==============================================================================


def main() -> int:
    try:
        findings = check_paths(sys.argv[1:])
    except ProgramError as error:
        print(f"[{PROGRAM}] {error}", file=sys.stderr)
        return STATUS_ERROR

    for finding in findings:
        print(f"[{PROGRAM}] [{finding.path}] {finding.message}", file=sys.stderr)

    return STATUS_FINDINGS if findings else STATUS_OK


if __name__ == "__main__":
    raise SystemExit(main())
