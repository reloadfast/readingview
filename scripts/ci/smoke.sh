#!/usr/bin/env bash
set -euo pipefail
: "${1:?Usage: smoke.sh IMAGE}"

# The image creates a fresh anonymous /data volume; no host appdata or ports.
container=$(docker create \
  -e SECRET_KEY=ci-disposable-smoke-key \
  -e DATABASE_URL=sqlite+aiosqlite:////data/readingview.db \
  "$1")
cleanup() {
  result=$?
  trap - EXIT
  if [ "$result" -ne 0 ]; then docker logs "$container" || true; fi
  docker rm -fv "$container" >/dev/null 2>&1 || true
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

wait_ready() {
  local attempt
  for attempt in $(seq 1 60); do
    if docker exec "$container" python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)" \
      >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo 'Readiness timeout' >&2
  return 1
}

docker start "$container" >/dev/null
wait_ready
docker exec -i "$container" python - <<'PY'
import json
import os
import re
import sqlite3
import urllib.request

assert (os.getuid(), os.getgid()) == (99, 100), "Expected application UID/GID 99:100"
base = "http://127.0.0.1:8000"
with urllib.request.urlopen(base + "/", timeout=5) as response:
    assert response.status == 200
    assert "text/html" in response.headers["Content-Type"]
    html = response.read().decode()
assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html)
assert assets, "Production frontend assets are missing"
for asset in assets:
    with urllib.request.urlopen(base + asset, timeout=5) as response:
        assert response.status == 200
        assert "text/html" not in response.headers["Content-Type"]
with sqlite3.connect("/data/readingview.db") as db:
    assert db.execute("SELECT version_num FROM alembic_version").fetchone()
with urllib.request.urlopen(base + "/api/settings", timeout=5) as response:
    settings = json.load(response)
assert settings["abs_url"] is None, "Smoke must not contact a configured ABS server"
request = urllib.request.Request(
    base + "/api/settings",
    data=json.dumps({"library_sort_default": "recently_added"}).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH",
)
with urllib.request.urlopen(request, timeout=5) as response:
    assert json.load(response)["library_sort_default"] == "recently_added"
PY

docker restart "$container" >/dev/null
wait_ready
docker exec "$container" python -c \
  "import json, urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/api/settings', timeout=5); assert json.load(r)['library_sort_default'] == 'recently_added'"
