# @path[src/lint_path/cli.py]
# ==============================================================================
# read the input, check paths against contracts, and print the verdict

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path as FsPath

from .constants import (
    PROGRAM,
    STATUS_ERROR,
    STATUS_OK,
    STATUS_REJECTED,
    msg,
)
from .core import ProjectionIndex, audit, gate, judge
from .rules import load_contract
from .schema import PathContract, PathContractError, PathFinding, ProgramError

# ==============================================================================
# PARSER
# ==============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=msg("cli.parser.description"),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="paths to check, empty means the audit root",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help=msg("cli.audit.help"),
    )
    parser.add_argument(
        "--domain",
        default=None,
        help=msg("cli.domain.help"),
    )
    parser.add_argument(
        "--root",
        default=".",
        help=msg("cli.root.help"),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help=msg("cli.format.help"),
    )
    return parser


# ==============================================================================
# OUTPUT
# ==============================================================================


def print_text(findings: Sequence[PathFinding]) -> None:
    for finding in findings:
        target = finding.path or finding.domain or PROGRAM
        print(f"[{PROGRAM}] [{target}] {finding.reason}")


def print_json(findings: Sequence[PathFinding], *, ok: bool) -> None:
    payload = {
        "version": 1,
        "ok": ok,
        "findings": [
            {
                "path": finding.path,
                "domain": finding.domain,
                "rule": finding.rule.name if finding.rule else None,
                "reason": finding.reason,
            }
            for finding in findings
        ],
    }
    print(json.dumps(payload, indent=2))


# ==============================================================================
# RUN
# ==============================================================================


def run(argv: Sequence[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = FsPath(args.root).resolve()

    try:
        findings = collect(args, root)
    except (PathContractError, ProgramError, OSError) as error:
        print(f"[{PROGRAM}] {error}", file=sys.stderr)
        return STATUS_ERROR

    if args.format == "json":
        print_json(findings, ok=not findings)
    else:
        print_text(findings)

    return STATUS_REJECTED if findings else STATUS_OK


def collect(args: argparse.Namespace, root: FsPath) -> list[PathFinding]:
    if args.audit:
        domain = FsPath(args.domain).resolve() if args.domain else None
        return audit(root, domain)

    if not args.paths:
        raise ProgramError(msg("cli.paths.missing"))

    if args.domain is not None:
        contract = load_contract(FsPath(args.domain).resolve())
        return check_contract(contract, args.paths)

    return check_gate(args.paths, root)


def check_contract(
    contract: PathContract,
    paths: Sequence[str],
) -> list[PathFinding]:
    findings: list[PathFinding] = []
    index = ProjectionIndex()

    for raw in paths:
        fs_path = FsPath(raw).resolve()
        verdict = judge(contract, fs_path, index)
        if not verdict.allowed:
            findings.append(
                PathFinding(
                    path=str(fs_path),
                    domain=contract.directory,
                    rule=verdict.rule,
                    reason=verdict.reason or "",
                )
            )

    return findings


def check_gate(paths: Sequence[str], root: FsPath) -> list[PathFinding]:
    findings: list[PathFinding] = []

    for raw in paths:
        fs_path = FsPath(raw).resolve()
        verdict = gate(fs_path, root)
        if not verdict.allowed:
            findings.append(
                PathFinding(
                    path=str(fs_path),
                    domain=None,
                    rule=verdict.rule,
                    reason=verdict.reason or "",
                )
            )

    return findings


def main() -> int:
    return run(sys.argv[1:])
