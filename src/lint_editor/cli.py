# @path[src/lint_editor/cli.py]
# ==============================================================================
# run the check and print one line per finding

import argparse
import sys

from .constants import PROGRAM, STATUS_ERROR, STATUS_FINDINGS, STATUS_OK, msg
from .core import check_paths
from .schema import ProgramError


# ==============================================================================
# COMMAND
# ==============================================================================
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=msg("cli.parser.description"),
    )
    parser.add_argument(
        "--ignore-file",
        action="append",
        help=msg("cli.ignore.help"),
    )
    parser.add_argument("paths", nargs="*", help=msg("cli.paths.help"))
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args(sys.argv[1:])
        findings = check_paths(args.paths, args.ignore_file)
    except ProgramError as error:
        print(f"[{PROGRAM}] {error}", file=sys.stderr)
        return STATUS_ERROR

    for finding in findings:
        print(f"[{PROGRAM}] [{finding.path}] {finding.message}", file=sys.stderr)

    return STATUS_FINDINGS if findings else STATUS_OK


if __name__ == "__main__":
    raise SystemExit(main())
