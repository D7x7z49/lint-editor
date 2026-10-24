#!/usr/bin/env bash
# @path[scripts/release.sh]
# ==============================================================================
# release: prepare, commit, push, wait for ci, tag, and push the tag
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

argument="${1:-patch}"

if [[ "$argument" == "current" ]]; then
  :
elif [[ "$argument" =~ ^[0-9] ]]; then
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

git add --all
if git diff --cached --quiet; then
  echo "no changes to commit" >&2
  exit 1
fi

git commit -m "chore(release): $tag"
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

git tag -a "$tag" -m "$tag"
git push origin "$tag"
