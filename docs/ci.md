# ReadingView CI

This repository adopts the source layout of
[Golden CI 4.0.0](https://forgejo.moseisley.es/Wind/global-standards/src/commit/64ec40904a302c81c23aeb51c9de1fb2292969ba/ci-cd),
updated November 3, 2026. Source revision:
`64ec40904a302c81c23aeb51c9de1fb2292969ba`.
Live runner adoption remains pending the checks below; local validation alone
does not establish production or runner compliance.

## Pipeline and source ownership

`.forgejo/workflows/ci.yml` handles PRs targeting main, pushes to main and manual
verification. One job installs frozen dependencies, runs project checks and
security checks, then builds one linux/amd64 candidate, smoke-tests it and scans
it. Any failure blocks publication. Runs serialize by repository/ref without
cancellation. There is one publisher for this image.

The following files are byte-for-byte copies from `ci-cd/scripts/` at the source
revision above; update them together from global-standards, without local edits:

- `scripts/ci/container.sh`
- `scripts/ci/publish.sh`
- `scripts/ci/prune_registry.py`

The workflow is adapted from `ci-cd/templates/ci.yml.template`. Project-specific
checks live in `verify.sh`, `security.sh` and `smoke.sh` in the same local folder.
The shared container script's `luma-ci-candidate` prefix is retained intentionally;
its full commit and random suffix make each candidate unique.

`verify.sh` uses Python 3.12 with `backend/uv.lock`, including the dev extra,
and pnpm 10.32.1 with `frontend/pnpm-lock.yaml`. The Dockerfile uses the same
Python runtime lock without dev extras and the same frozen frontend install.
Update Python dependencies deliberately with `cd backend && uv lock`, review
the lock diff, and run the checks before committing. NumPy remains optional
and absent from the base development environment.

Required project checks are Ruff lint/format, the established root-level mypy
invocation, pytest with the existing configured 80% backend coverage threshold,
ESLint, Prettier, TypeScript, non-watch Vitest tests, the production frontend
build and Python 3.12 OpenAPI regeneration/diff. Generated API files are excluded
from Prettier because the API generator owns their formatting. Existing frontend
tests run without an invented coverage claim; expanding coverage is separate work.
Coverage traces threads and greenlets so SQLAlchemy's asynchronous transaction
switches do not hide executed application lines. The existing Prettier settings
are enforced across the frontend after a one-time formatting pass; generated
Vite config output is excluded alongside generated API types.

Gitleaks scans the working tree with redaction, including source, tracked
configuration and CI. Its configuration excludes dependency/build/test caches,
not application source. Bandit scans both backend application modules. pip-audit
audits the installed locked environment including dev tooling and fails on any
advisory. It exports the actual installed distribution versions and excludes only
ReadingView itself, which is unpublished editable source; no dependency is
resolved again or skipped. pnpm audit gates HIGH and CRITICAL findings including dev dependencies.
Trivy scans vulnerabilities and secrets in the local Docker candidate with
HIGH/CRITICAL and exit-code 1. Tool/service failures are failures; no blanket
unfixed-vulnerability exclusions or advisory exceptions are configured. The
initial lock preserves the existing Python environment except security-patched
packages. Vite is pinned to 8.2.4; targeted pnpm overrides patch source-map-js,
undici 8 and the React Hooks lint plugin's Zod dependency.

The smoke adapter uses the image's UID/GID 99:100, a disposable anonymous `/data`
volume and a generated container name. It waits for health, verifies migrations,
settings and built static assets, writes a harmless preference, restarts the
same disposable container and verifies persistence. It removes only that
container and its anonymous volume. It exposes no host port and uses no ABS,
Ollama, notification or production service.

## Runner prerequisites

`ubuntu-latest` preserves the existing label on the self-hosted `unraid-runner`;
it does not request a GitHub runner or establish its installed tools. Before
enabling this workflow, infrastructure must verify that label's mapping to a
maintained internal runner image pinned by digest and record that digest and
tool versions in its inventory. This repository cannot establish that mapping
from workflow source alone.

The maintained image must supply Python 3.12 (and Python 3.12+ as `python3` for
retention), uv 0.10.0, Node 22.12+, pnpm 10.32.1, Git, Bash, curl, jq, Docker CLI
with Buildx supporting `imagetools create --prefer-index=false`, Gitleaks with
`dir` and `[[allowlists]]` support, and Trivy. Infrastructure must pin the scanner
versions/images and verify database downloads or internal mirrors. There are no
per-run runtime, scanner, OS or browser installers. The adapter fails if Node
or pnpm differs or Python 3.12 is absent; uv Python downloads are disabled.

Checkout is pinned to the mirrored actions/checkout v4.3.1 commit
`34e114876b0b11c390a56381ad16ebd13914f8d5`, whose action metadata uses Node 20;
the Forgejo runner must also support that action runtime. The action uses the
automatic workflow token, full history and `persist-credentials: false`.

Verify internal Forgejo TLS, REST API routing, DinD DNS, default-builder access
and the centrally managed Docker Hub pull mirror on the actual runner. No
application workflow configures DNS, a registry cache, a broad Docker prune or
a new public service. Browser/OS dependencies are excluded from routine CI.

## Publication and retention

Only a successful `push` to `refs/heads/main` receives the Actions secret
`FORGEJO_TOKEN`, scoped to the publishing step. PRs and manual runs verify only.
The secret must already exist at repository/organization level and grant
repository read plus package read/write/delete for owner `wind`; authentication
identity is `Wind`. No secret creation or value inspection is part of adoption.

The publisher uses a temporary Docker config, rejects existing full-SHA tags,
checks remote main before pushing/promoting, pushes the tested candidate as
`forgejo.moseisley.es/wind/readingview:sha-<full commit>`, promotes its registry
digest to `latest` and verifies equality. Push, promotion and digest reads have
bounded retries. Successful logs record commit and digest. A SHA tag is a
write-once policy, while the digest is the exact rollback identity.

After verified publication the shared publisher applies package-scoped
retention: latest/current full-SHA plus two older distinct release digests,
preserving referenced child manifests and supporting historical short SHA tags.
This normally leaves four visible tags for three releases. Other old tags and
buildcache aliases are eligible for deletion. Local candidate cleanup is scoped
to this run; infrastructure owns global Docker cleanup.

Before live adoption, review deployed/pinned digests and any semver or longer
rollback requirements against that three-release window. No live inventory or
fleet safety is inferred from the local checkout. If protected releases require
a longer window, resolve the policy upstream before enabling publication.
The shared publisher is intentionally unchanged and will apply this policy on
the first successful main publication; merging/enabling it requires that review.

For retention recovery, use the shared script's default dry-run with the exact
published revision and digest, in an authorized environment with `IMAGE`,
`REGISTRY`, `REGISTRY_USERNAME` and `FORGEJO_TOKEN`. Review its plan before
explicit `--apply`. Retention failure fails CI after publication; it does not
undo the verified image. Recover retention separately rather than re-pushing
an existing SHA tag. Registry publication never restarts the production app.

## Live adoption gates

Before marking compliance complete or changing required merge checks:

1. Verify the pinned runner/tool inventory, Actions secret scope, internal
   network, default Docker builder and Buildx/registry compatibility.
2. Run a real PR and a manual verification; confirm build/smoke/scan run without
   publish credentials or registry changes. Force a check and smoke failure and
   confirm publication stays blocked.
3. Review the rollback window and run retention dry-run against the exact image.
   Exercise the shared offline failure/race checks before authorizing deletion.
4. On an authorized main push, verify the logged digest and latest equality,
   run-owned cleanup, concurrent serialization and stale-run rejection. Verify
   rate-limit backoff, retained rollback digests and child manifests on the
   actual DinD/Forgejo topology.

No publication, package deletion, secret configuration, runner provisioning,
production restart or remote canary is performed by the source adaptation.

## Local validation (November 4, 2026)

- Python 3.12.12: 313 backend tests pass, 82.87% application coverage; Ruff,
  formatting, mypy, Bandit and strict installed-dependency audit pass.
- Node 22.21.1 / pnpm 10.32.1: frontend formatting, lint, types, five Vitest
  tests and production build pass. pnpm audit passes the HIGH/CRITICAL gate;
  two MODERATE findings remain below that configured threshold.
- Python 3.12 OpenAPI output generates byte-identical committed API types.
- All 30 upstream offline publication/retention checks pass against the copied
  shared scripts, which also match upstream byte-for-byte. Workflow structure,
  shell syntax, embedded smoke Python and Gitleaks TOML syntax are checked.
- Docker/Buildx, Trivy and Gitleaks executables are unavailable locally. Actual
  image build/smoke/scans, publication, retention and runner configuration remain
  live adoption gates; no success is claimed for them.
