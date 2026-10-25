#!/usr/bin/env bash
# @path[scripts/release.sh]
# ==============================================================================
# release: check, test, bump, commit, push, wait for ci, tag, and push the tag
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

argument="${1:-patch}"

# ==============================================================================
# PRECONDITIONS
# ==============================================================================

branch="$(git branch --show-current)"
if [[ "$branch" != "main" ]]; then
  echo "release must run on main, current branch is $branch" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "worktree is not clean, commit or stash changes first" >&2
  git status --short >&2
  exit 1
fi

git fetch origin main

behind="$(git rev-list --count HEAD..origin/main)"
if [[ "$behind" != "0" ]]; then
  echo "local main is behind origin/main by $behind commits" >&2
  exit 1
fi

command -v gh >/dev/null || {
  echo "gh is required to watch the ci run" >&2
  exit 1
}

# ==============================================================================
# CHECKS
# ==============================================================================

uv run pytest
uv run pre-commit run --all-files

# ==============================================================================
# VERSION
# ==============================================================================

if [[ "$argument" == "current" ]]; then
  :
elif [[ "$argument" =~ ^[0-9] ]]; then
  uv version "$argument"
else
  uv version --bump "$argument"
fi

uv lock

version="$(uv version --short)"
tag="v$version"

uv run python - "$tag" <<'PY'
import pathlib
import re
import sys

tag = sys.argv[1]
path = pathlib.Path("README.md")
text = path.read_text(encoding="utf-8")
text, count = re.subn(r"(?m)^(\s*rev:\s*)v\S+\s*$", rf"\g<1>{tag}\n", text)
if count != 1:
    raise SystemExit(f"expected one rev line in README.md, found {count}")
path.write_text(text, encoding="utf-8")
PY

# ==============================================================================
# COMMIT
# ==============================================================================

git add pyproject.toml uv.lock README.md
if git diff --cached --quiet; then
  echo "no changes to commit" >&2
  exit 1
fi

git commit -m "chore: release $tag and update the readme revision"

# ==============================================================================
# PUSH AND CI
# ==============================================================================

git push origin HEAD

commit="$(git rev-parse HEAD)"
echo "waiting for ci on $commit"

run_id=""
for _ in $(seq 1 30); do
  run_id="$(gh run list --commit "$commit" --workflow ci.yml --limit 1 \
    --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)"
  if [[ -n "$run_id" ]]; then
    break
  fi
  sleep 10
done

if [[ -z "$run_id" ]]; then
  echo "no ci run found for $commit" >&2
  exit 1
fi

gh run watch --exit-status "$run_id"

# ==============================================================================
# TAG
# ==============================================================================

git tag -a "$tag" -m "$tag"
git push origin "$tag"
