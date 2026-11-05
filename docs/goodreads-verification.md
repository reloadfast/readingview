# Goodreads import verification

Verified on 2026-11-05 for delivery step 5 in
[goodreads-import-plan.md](goodreads-import-plan.md).

## Automated checks

| Check | Result |
| --- | --- |
| Full backend pytest suite on Python 3.12.12 | 373 passed; 83.91% coverage; 80% gate met |
| Ruff lint and format checks over `backend/` | Passed |
| Mypy from repository root over `backend/` | Passed |
| Bandit over `backend/app` and `backend/book_recommender` | Passed |
| Frontend ESLint and Prettier checks | Passed |
| Frontend TypeScript checks | Passed |
| Frontend Vitest suite | 24 passed |
| Frontend production build | Passed |
| Python 3.12 OpenAPI export and frontend regeneration | Both generated files identical to their pre-check contents |

Bandit initially flagged the assertion left in the prototype's Goodreads URL
validation. The service now uses the captured book ID from its checked regex
match directly. Ruff, mypy, Bandit, and the complete backend suite passed after
that change. No API contract change resulted from the fix.

The environment has Node 25.9.0 and pnpm 10.32.1. Frontend commands emit the
existing Node 24 engine warning, and the build emits its existing large-chunk
warning. Checks passed, but this does not reproduce CI's Node 24 runtime.
Existing Pydantic/Alembic deprecation warnings remain. SQLite migration setup
stalls inside the execution sandbox, so backend database tests ran successfully
outside it with temporary databases and mocked external calls.

The generated files were saved before re-exporting OpenAPI using Python 3.12.
The normal `pnpm openapi --spec-path ...` command was then run and both files
were compared byte-for-byte to those saved copies. This confirms regeneration
parity of the working feature contract; the intended new endpoint/types still
appear in the feature diff against the repository baseline.

Dependency vulnerability audits, image builds/scans, and publication were not
run for this local verification step. Dependencies, CI, registry, and deployment
configuration were not changed. Normal delivery CI remains applicable.

## Browser environment

Chromium exercised the built SPA served by the actual FastAPI app on a
temporary loopback server. The database was a dedicated SQLite file under
`/tmp/readingview-goodreads-verification`, initialized with `alembic upgrade head`.
Cover uploads used a separate directory under the same temporary root.
Background jobs and ABS connections were disabled; the existing Upcoming tab
could report the absence of ABS configuration in this isolated environment.

Only Goodreads HTTP transport was replaced with deterministic responses. The
real Goodreads fetch/parser, import orchestration, API validation, existing-entry
query, save/duplicate handling, file storage, and calendar export were exercised.
Fixture pages used the demonstrated title, author, series, date, and Ebook
format, plus partial, bot-challenge, and delayed-response cases. A cover image
was uploaded locally rather than fetched from a remote image host.

Desktop viewport: 1440 × 1100. Mobile viewport: 390 × 844. Both light and dark
themes were inspected. The temporary browser/server processes were stopped
after verification. No request targeted production, ABS, or the live Goodreads
service; saved/edited/archived records belonged only to the temporary database.

## Browser acceptance results

| Scenario | Observed result |
| --- | --- |
| Import submitted with Enter in the URL input | Editor populated with the full title, author, series, number 6, Ebook, and 2027-08-17 |
| Inspect draft before Save | Database unchanged |
| Change title and select Audiobook instead of Ebook | Corrections retained; original edition date stayed editable and unchanged |
| View an archived owned match | Relevant filters enabled; selected row scrolled into view and received keyboard focus |
| Navigate to an existing match after editing the draft | Draft edits and stored existing-entry fields/notes preserved |
| Save reviewed draft | One new SQLite record created with selected medium, source link, and checked timestamp |
| Export saved release calendar | HTTP 200; event date matched 2027-08-17 |
| Attempt exact duplicate Save | Existing 409 message displayed; corrected draft retained |
| Bot challenge returned with HTTP 202 | Actionable inline error; retry available; manual fallback retained only the supplied link |
| Partial metadata | Available title populated; missing date and medium remained blank/unselected |
| Cancel delayed lookup, reopen manual entry, wait for old response | New manual edits remained intact; canceled import did not reopen |
| Edit an existing imported entry | Existing fields prefilled; note update saved correctly |
| Upload and retrieve cover from editor | File upload and cover request succeeded |
| Archive and restore a local imported entry | Visibility and archive action updated correctly |
| Mobile review and Save controls | Reachable by scrolling; no horizontal overflow of the page or main content |
| Browser runtime errors | None observed |

Screenshots were captured as local review artifacts for desktop import review,
existing-entry navigation, and mobile source/editor views. They contain only
synthetic local test data.

## Remaining delivery check

Step 6 remains open: perform a read-only lookup from the intended deployed
ReadingView environment to establish Goodreads access there. The user's earlier
successful run on Fijo establishes access from Fijo, not necessarily from the
deployed container. The local browser results establish application behavior
with controlled upstream responses and do not claim live-service availability.
No production save, deployment, or publication has been performed.
