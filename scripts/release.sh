#!/usr/bin/env bash
# @path[scripts/release.sh]
# release: bump the version, sync the readme, commit, tag, and push
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

argument="${1:-patch}"

if [[ "$argument" =~ ^[0-9] ]]; then
  uv version "$argument"
else
  uv version --bump "$argument"
fi

version="$(uv version --short)"
tag="v$version"

uv run python - "$tag" <<'PY'
import pathlib
import re
import sys

tag = sys.argv[1]
path = pathlib.Path("README.md")
text = path.read_text()
text, count = re.subn(r"(?m)^(\s*rev:\s*)v\S+\s*$", rf"\g<1>{tag}\n", text)
if count != 1:
    raise SystemExit(f"expected one rev line in README.md, found {count}")
path.write_text(text)
PY

git add -- README.md pyproject.toml uv.lock
git commit -m "chore(release): $tag"
git tag -a "$tag" -m "$tag"
git push origin HEAD --follow-tags
