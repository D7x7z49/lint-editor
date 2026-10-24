# @path[src/lint_commit/cli.py]
# ==============================================================================
# read the commit message, gather the staged paths, and print the verdict

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from .constants import (
    CONFIG_DIRS,
    CONFIG_FILE,
    PROGRAM,
    STATUS_ERROR,
    STATUS_OK,
    STATUS_REJECTED,
    msg,
)
from .core import check
from .rules import find_config, load_config
from .schema import ProgramError

# ==============================================================================
# GIT
# ==============================================================================


def git(cwd: Path, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ("git", *args),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise ProgramError(msg("git.run.failed", reason=error)) from error


def staged_paths(cwd: Path) -> tuple[str, ...]:
    # renames are split into a delete and an add, so both sides are checked
    result = git(
        cwd,
        (
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "--diff-filter=ACMRD",
        ),
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or "git diff failed"
        raise ProgramError(msg("git.read.failed", reason=reason))
    return tuple(line for line in result.stdout.splitlines() if line)


def is_merge(cwd: Path) -> bool:
    result = git(cwd, ("rev-parse", "-q", "--verify", "MERGE_HEAD"))
    return result.returncode == 0


def is_fixup(message: str) -> bool:
    first = message.split("\n", 1)[0]
    return first.startswith(("fixup! ", "squash! "))


# ==============================================================================
# COMMAND
# ==============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=msg("cli.parser.description"),
    )
    parser.add_argument(
        "--config",
        default=None,
        help=msg("cli.config.help"),
    )
    parser.add_argument(
        "message_file",
        nargs="?",
        help=msg("cli.message.help"),
    )
    return parser


def read_message(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ProgramError(
            msg("message.file.failed", path=path, reason=error)
        ) from error


def run(argv: Sequence[str]) -> int:
    args = build_parser().parse_args(argv)
    cwd = Path.cwd()

    message_path = (
        Path(args.message_file)
        if args.message_file
        else cwd / ".git" / "COMMIT_EDITMSG"
    )
    text = read_message(message_path)

    if is_fixup(text):
        return STATUS_OK

    if is_merge(cwd):
        return STATUS_OK

    if args.config is not None:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = cwd / config_path
    else:
        found = find_config(cwd)
        if found is None:
            candidates = ", ".join(
                f"{part}/{CONFIG_FILE}" if part else CONFIG_FILE for part in CONFIG_DIRS
            )
            raise ProgramError(msg("config.file.missing", paths=candidates))
        config_path = found

    config = load_config(config_path)
    paths = staged_paths(cwd)
    verdict = check(text, config, paths)

    if verdict.passed:
        return STATUS_OK

    print(f"[{PROGRAM}] {verdict.detail}", file=sys.stderr)
    return STATUS_REJECTED


def main() -> int:
    try:
        return run(sys.argv[1:])
    except ProgramError as error:
        print(f"[{PROGRAM}] {error}", file=sys.stderr)
        return STATUS_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
