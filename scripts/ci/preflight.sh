#!/usr/bin/env bash
set -euo pipefail

# Report the whole inventory before dependency work, rather than failing on one
# missing executable at a time. Provision tools in docker/ci, never in this job.
missing=()
for tool in node pnpm uv python3 git docker gitleaks trivy jq curl; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing+=("$tool")
  fi
done
if [ "${#missing[@]}" -ne 0 ]; then
  printf 'CI tool image is incomplete; missing: %s\n' "${missing[*]}" >&2
  echo 'Use the digest-pinned tool image from docker/ci/Dockerfile; see docs/ci.md.' >&2
  exit 1
fi

node -e 'if (process.versions.node.split(".")[0] !== "24") throw new Error(`CI requires Node 24; found ${process.version}`)'
test "$(pnpm --version)" = 10.32.1
test "$(uv --version | cut -d ' ' -f 2)" = 0.13.5
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "CI requires Python 3.12"'
UV_PYTHON_DOWNLOADS=never uv python find 3.12 >/dev/null
docker buildx version
gitleaks version
trivy --version
