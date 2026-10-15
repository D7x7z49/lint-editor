# @path[src/lint_editor/cli.py]

import sys

from .constants import PROGRAM
from .core import check_paths
from .errors import ProgramError

STATUS_OK = 0
STATUS_FINDINGS = 1
STATUS_ERROR = 2


def main() -> int:
    try:
        findings = check_paths(sys.argv[1:])
    except ProgramError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return STATUS_ERROR

    for finding in findings:
        print(f"{finding.path}: {finding.message}", file=sys.stderr)

    return STATUS_FINDINGS if findings else STATUS_OK


if __name__ == "__main__":
    raise SystemExit(main())
