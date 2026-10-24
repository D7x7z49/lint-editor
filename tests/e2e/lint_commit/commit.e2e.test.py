# @path[tests/e2e/lint_commit/commit.e2e.test.py]

import subprocess
from collections.abc import Callable
from pathlib import Path

EXIT_REJECTED = 1


def test_split_is_rejected(
    e2e_case: Callable[..., Path],
    run_cli: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    repo = e2e_case("lint_commit/split", ("src/api/a.py", "docs/b.md"))
    result = run_cli(repo, "lint_commit", "--config", "commit-config.toml", "msg.txt")

    assert result.returncode == EXIT_REJECTED
    assert "allowed type set is empty" in result.stderr
