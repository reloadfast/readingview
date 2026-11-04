"""Retain three distinct releases of the configured image; dry-run unless --apply."""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
SHA_TAG = re.compile(r"sha-[0-9a-f]{7,40}")
MEDIA_TYPES = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Refusing authenticated registry redirect")


class Client:
    def __init__(self, registry, owner, token, name, username, *, sleep=time.sleep):
        if not re.fullmatch(r"[a-zA-Z0-9.-]+(?::[0-9]+)?", registry):
            raise ValueError("Invalid registry host")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", owner):
            raise ValueError("Invalid package owner")
        if not token or any(c in token for c in "\r\n"):
            raise ValueError("Missing or invalid package token")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._/-]*", name) or any(
            part in {"", ".", ".."} for part in name.split("/")
        ):
            raise ValueError("Invalid container package name")
        if not username or any(c in username for c in "\r\n:"):
            raise ValueError("Invalid registry username")
        self.owner = owner
        self.name = name
        self.username = username
        self.origin = f"https://{registry}"
        self.package = f"/api/v1/packages/{quote(owner)}/container/{quote(name, safe='')}"
        self.repository = f"/v2/{owner.lower()}/{name}/manifests/"
        self.token = token
        self.sleep = sleep
        self.opener = build_opener(NoRedirects())

    def request(self, path, method="GET", *, registry=False, missing_ok=False):
        auth = "token " + self.token
        if registry:
            auth = "Basic " + base64.b64encode(f"{self.username}:{self.token}".encode()).decode()
        request = Request(
            self.origin + path,
            method=method,
            headers={
                "Authorization": auth,
                "Accept": MEDIA_TYPES if registry else "application/json",
            },
        )
        for attempt in range(5):
            delay = 15 * 2**attempt
            try:
                with self.opener.open(request, timeout=30) as response:
                    return response.read()
            except HTTPError as error:
                if error.code == 404 and missing_ok:
                    return None
                if error.code not in {429, 500, 502, 503, 504}:
                    raise RuntimeError(f"Package API {method} failed: HTTP {error.code}") from None
                retry = error.headers.get("Retry-After", "")
                try:
                    seconds = int(retry)
                except ValueError:
                    try:
                        seconds = (parsedate_to_datetime(retry) - datetime.now(UTC)).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        seconds = 0
                # If the server requires a longer wait, stop rather than retry too soon.
                if seconds > 300:
                    raise RuntimeError(
                        "Registry requested a retry delay over five minutes"
                    ) from None
                delay = max(delay, seconds)
            except (URLError, TimeoutError):
                pass
            if attempt == 4:
                raise RuntimeError(f"Package API {method} failed after five attempts")
            print(f"Package API retry in {delay:g}s", flush=True)
            self.sleep(delay)
        raise AssertionError("Unreachable")

    def versions(self):
        packages = []
        seen = set()
        for page in range(1, 1001):
            query = urlencode({"type": "container", "q": self.name, "limit": 100, "page": page})
            rows = json.loads(self.request(f"/api/v1/packages/{quote(self.owner)}?{query}"))
            if not isinstance(rows, list):
                raise ValueError("Malformed package inventory")
            if not rows:
                return packages
            for row in rows:
                if row["id"] in seen:
                    raise ValueError("Repeated package pagination; refusing incomplete inventory")
                seen.add(row["id"])
                if row["type"] == "container" and row["name"] == self.name:
                    if row["owner"]["login"].lower() != self.owner.lower():
                        raise ValueError("Unexpected package owner")
                    packages.append(row)
        raise ValueError("Package pagination limit exceeded")

    def digest(self, version):
        files = json.loads(self.request(f"{self.package}/{quote(version, safe='')}/files"))
        manifests = [f for f in files if f["name"] == "manifest.json"]
        if len(manifests) != 1 or not re.fullmatch(r"[0-9a-f]{64}", manifests[0]["sha256"]):
            raise ValueError("Package has no unique, valid manifest")
        return "sha256:" + manifests[0]["sha256"]

    def manifest(self, digest):
        if not DIGEST.fullmatch(digest):
            raise ValueError("Invalid manifest digest")
        raw = self.request(self.repository + digest, registry=True)
        if "sha256:" + hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Registry manifest content digest mismatch")
        manifest = json.loads(raw)
        if manifest.get("schemaVersion") != 2:
            raise ValueError("Unsupported registry manifest")
        return manifest

    def delete(self, version):
        # Delete the package VERSION, never a shared registry blob or manifest digest.
        self.request(f"{self.package}/{quote(version, safe='')}", "DELETE", missing_ok=True)


def plan(client, revision, expected_digest):
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or not DIGEST.fullmatch(expected_digest):
        raise ValueError("Expected full commit and published digest are required")
    rows = client.versions()
    versions = {row["version"]: row for row in rows}
    if len(versions) != len(rows):
        raise ValueError("Duplicate package versions")
    current = "sha-" + revision
    if not {"latest", current} <= versions.keys():
        raise ValueError("Published latest/SHA tags are missing")
    if any(row["id"] > versions["latest"]["id"] for row in rows):
        raise ValueError("Newer package publication is in progress; refusing retention")
    if client.digest("latest") != expected_digest or client.digest(current) != expected_digest:
        raise ValueError("Published latest/SHA digest mismatch; refusing retention")
    keep = {"latest", current}
    digests = {expected_digest}
    candidates = sorted(
        (row for row in rows if SHA_TAG.fullmatch(row["version"]) and row["version"] != current),
        key=lambda row: (datetime.fromisoformat(row["created_at"]), row["id"]),
        reverse=True,
    )
    for row in candidates:
        digest = client.digest(row["version"])
        if digest not in digests:
            keep.add(row["version"])
            digests.add(digest)
        if len(digests) == 3:
            break
    # Legacy Buildx indexes reference hidden child package versions (including
    # attestations). Preserve their complete manifest graph, not just visible tags.
    pending = list(digests)
    visited = set()
    while pending:
        digest = pending.pop()
        if digest in visited:
            continue
        if len(visited) >= 100:
            raise ValueError("Unexpectedly large manifest graph")
        visited.add(digest)
        manifest = client.manifest(digest)
        for child in manifest.get("manifests", []):
            if not DIGEST.fullmatch(child["digest"]):
                raise ValueError("Invalid child manifest digest")
            pending.append(child["digest"])
    keep.update(digest for digest in visited if digest in versions)
    # A fixed snapshot avoids pagination shifts while deleting and never includes
    # a package created by a later publication.
    remove = [row["version"] for row in rows if row["version"] not in keep]
    return sorted(keep), remove


def prune(client, revision, expected_digest, *, apply=False):
    keep, remove = plan(client, revision, expected_digest)
    print("Retain: " + ", ".join(keep), flush=True)
    print(
        f"{'Delete' if apply else 'Would delete'} {len(remove)} obsolete package versions",
        flush=True,
    )
    if not apply:
        return keep, remove
    for version in remove:
        # A changed latest (another writer) aborts before the next deletion.
        if client.digest("latest") != expected_digest:
            raise ValueError("Latest changed during retention; stopping")
        client.delete(version)
        print("Deleted package version: " + version, flush=True)
        client.sleep(1)
    if (
        client.digest("latest") != expected_digest
        or client.digest("sha-" + revision) != expected_digest
    ):
        raise ValueError("Published tags changed during retention")
    # Re-read both inventory and all retained manifest graphs after deletion so
    # a present tag with missing platform/attestation content cannot pass.
    verified_keep, obsolete = plan(client, revision, expected_digest)
    if obsolete or set(verified_keep) != set(keep):
        raise ValueError("Registry retention verification failed (possibly a concurrent writer)")
    print("Registry retention verified", flush=True)
    return keep, remove


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    registry = os.environ["REGISTRY"]
    image = os.environ["IMAGE"]
    prefix = registry + "/"
    if not image.startswith(prefix):
        raise ValueError("Image must belong to the configured registry")
    owner, separator, name = image[len(prefix) :].partition("/")
    if not separator or owner != owner.lower():
        raise ValueError("Image must specify a lowercase package owner and name")
    client = Client(
        registry, owner, os.environ["FORGEJO_TOKEN"], name, os.environ["REGISTRY_USERNAME"]
    )
    prune(client, args.revision, args.digest, apply=args.apply)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, RuntimeError, ValueError, TypeError) as error:
        print(f"Registry retention failed: {error}", file=sys.stderr)
        sys.exit(1)
