#!/usr/bin/env bash
set -euo pipefail
: "${IMAGE:?}" "${REGISTRY:?}" "${REGISTRY_USERNAME:?}"
: "${CI_LOCAL_IMAGE:?Build step must pass}" "${CI_REVISION:?}"
: "${FORGEJO_TOKEN:?Forgejo Actions secret FORGEJO_TOKEN is required}"
if [[ ${GITHUB_EVENT_NAME:-} != push || ${GITHUB_REF:-} != refs/heads/main ]]; then
  echo 'Only a main push may publish' >&2
  exit 1
fi
work=$(mktemp -d)
export DOCKER_CONFIG="$work/docker"
mkdir -p "$DOCKER_CONFIG"
cleanup() {
  docker image rm "$CI_LOCAL_IMAGE" "${IMAGE}:sha-${CI_REVISION}" >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
check_head() {
  local head
  head=$(git ls-remote origin refs/heads/main | awk '{print $1}')
  [[ $head == "$CI_REVISION" ]] || { echo 'Refusing stale main publication' >&2; return 1; }
}
# persist-credentials:false means private fetches need an explicit temporary header.
# The Actions secret stays in memory and is never written to GITHUB_ENV.
registry_token=$FORGEJO_TOKEN
unset FORGEJO_TOKEN
# Prevent workflow-command injection through a malformed secret.
[[ $registry_token != *$'\n'* && $registry_token != *$'\r'* ]] || exit 1
printf '::add-mask::%s\n' "$registry_token"
# Use an environment-scoped git config, not persistent credentials in the checkout.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=http.extraHeader
GIT_CONFIG_VALUE_0="Authorization: Basic $(printf '%s:%s' "$REGISTRY_USERNAME" "$registry_token" | base64 | tr -d '\n')"
export GIT_CONFIG_VALUE_0
printf '::add-mask::%s\n' "${GIT_CONFIG_VALUE_0#Authorization: Basic }"
printf '%s' "$registry_token" | docker login "$REGISTRY" -u "$REGISTRY_USERNAME" --password-stdin
check_head
# Distinguish a missing manifest from auth, network and other registry failures.
sha_image="${IMAGE}:sha-${CI_REVISION}"
if docker buildx imagetools inspect "$sha_image" >"$work/existing" 2>"$work/inspect-error"; then
  echo 'SHA tag already exists; use explicit digest promotion, never overwrite it' >&2
  exit 1
elif ! grep -Eqi 'manifest unknown|no such manifest|: not found([[:space:]]|$)' "$work/inspect-error"; then
  cat "$work/inspect-error" >&2
  exit 1
fi
docker tag "$CI_LOCAL_IMAGE" "$sha_image"
for attempt in 1 2 3 4 5; do
  if docker push "$sha_image"; then break; fi
  if [[ $attempt == 5 ]]; then echo 'SHA push failed after five attempts' >&2; exit 1; fi
  sleep "$((15 * (1 << (attempt - 1))))"
done
registry_retry() {
  local attempt
  for attempt in 1 2 3 4 5; do
    if "$@"; then return 0; fi
    if [[ $attempt == 5 ]]; then
      echo 'Registry operation failed after five attempts' >&2
      return 1
    fi
    sleep "$((15 * (1 << (attempt - 1))))"
  done
}
# Obtain and pin the registry manifest digest; do not promote from a mutable tag.
digest=$(registry_retry docker buildx imagetools inspect "$sha_image" --format '{{json .Manifest}}' | jq -er '.digest | select(test("^sha256:[0-9a-f]{64}$"))')
promote_latest() {
  # A stale head is terminal; check it again after every registry backoff.
  check_head || exit 1
  docker buildx imagetools create --prefer-index=false --tag "${IMAGE}:latest" "${IMAGE}@${digest}"
}
registry_retry promote_latest
alias_digest=$(registry_retry docker buildx imagetools inspect "${IMAGE}:latest" --format '{{json .Manifest}}' | jq -er '.digest')
[[ $alias_digest == "$digest" ]] || { echo 'latest digest verification failed' >&2; exit 1; }
printf 'Published commit %s as %s@%s\n' "$CI_REVISION" "$IMAGE" "$digest"
# Only this configured image is eligible, after verified promotion and a head check.
check_head
FORGEJO_TOKEN=$registry_token python3 scripts/ci/prune_registry.py \
  --revision "$CI_REVISION" --digest "$digest" --apply
unset registry_token
