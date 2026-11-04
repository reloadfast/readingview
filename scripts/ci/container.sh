#!/usr/bin/env bash
# Shared golden CI 2.0.0; project adapters supply checks and smoke behavior.
set -euo pipefail
: "${GITHUB_ENV:?Workflow environment file is required}"
revision=$(git rev-parse HEAD)
# A random suffix avoids collisions between PRs, re-runs and parallel repositories.
work=$(mktemp -d)
local_image="luma-ci-candidate:${revision}-${work##*.}"
cleanup() {
  docker image rm "$local_image" >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# The default Docker driver shares this DinD daemon's bounded local build cache.
docker buildx build --builder default --platform linux/amd64 --load \
  --provenance=false --build-arg "GIT_SHA=$revision" \
  --label "org.opencontainers.image.revision=$revision" --tag "$local_image" .
bash scripts/ci/smoke.sh "$local_image"
trivy image --image-src docker --scanners vuln,secret --severity HIGH,CRITICAL \
  --exit-code 1 --no-progress "$local_image"
# Keep only the passing candidate for the next step. It is never rebuilt.
printf 'CI_LOCAL_IMAGE=%s\nCI_REVISION=%s\n' "$local_image" "$revision" >> "$GITHUB_ENV"
trap - EXIT
rm -rf "$work"
