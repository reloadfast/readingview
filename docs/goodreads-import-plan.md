# Goodreads release import plan

Date: 2026-11-05. Status: steps 1–5 complete; deployment-environment access check pending.

## Objective and agreed scope

Let the user create a watched release by pasting a Goodreads book link, reviewing
the extracted details in the existing release editor, and explicitly saving it.
Keep a separate manual addition path with the current blank form.

The user confirmed these decisions on 2026-11-05:

1. Import once at creation. No refresh action or scheduled Goodreads polling.
2. Import the linked edition's format and date. Both remain editable, including
   when the user wants to track an audiobook instead of the linked ebook.
3. Warn and provide an action to view existing entries for the same Goodreads
   book. Allow tracking a different medium.

The source-link warning is advisory; the existing author/title/date/media
duplicate constraint remains the final save-time rule. This does not introduce
a new uniqueness constraint, a separate imported-release model, or a migration.

## Evidence and limits

The reusable service lives in `backend/app/services/goodreads.py`; the diagnostic
CLI is `backend/app/services/goodreads_probe.py`. Usage and access findings are
in [goodreads-prototype.md](goodreads-prototype.md).

The user's run on Fijo successfully fetched book ID `257149406` with HTTP 200
and extracted:

| Field | Observed value | Source |
| --- | --- | --- |
| Title | Bog Standard Isekai: Towering - A LitRPG Isekai Adventure | Next.js |
| Author | Miles English | Next.js |
| Series | Bog Standard Isekai | Next.js |
| Series number | 6 | Next.js |
| Release date | 2027-08-17 | Next.js |
| Medium | Ebook | JSON-LD |
| Cover | Goodreads-provided image URL | Next.js |

The response was 159,588 bytes. The canonical source link was
`https://www.goodreads.com/book/show/257149406`.

An earlier request from the agent's execution environment received HTTP 202
with bot verification. Fijo's success demonstrates feasibility from that
machine, not guaranteed access from the deployed container. Parser tests
currently use synthetic fixtures; the successful report is not an HTML capture.

## User experience requirements

### GR-001: Two addition paths

- Keep the entry point in Releases > Manual Tracking.
- Add release exposes clearly labeled Manual and From Goodreads choices.
- Manual opens the existing empty editor.
- From Goodreads opens a labeled URL input and a Fetch details action.
- Show a loading state and prevent duplicate submissions while fetching.
- No record is written during lookup or draft review. Cancel discards the draft.

### GR-002: Review before saving

- A usable lookup populates the existing editor rather than immediately saving.
- All imported fields remain editable. Preserve the full source title; do not
  automatically remove series text or subtitles.
- Show the source link and relevant data-quality warnings above the editor.
- Display a concise reminder that the date belongs to the linked edition.
- Missing fields remain blank. Standalone books without series information are
  valid; absent optional metadata must not prevent review or saving.
- Status defaults to Watching. Comments remain empty and user-authored.
- Use the existing create endpoint and cover-upload behavior when saving.
- Imported entries appear in the same list and participate in the existing
  calendar, editing, status, and archive behavior.

### GR-003: Edition and medium handling

- Populate the linked edition's date and recognized medium without translating
  that date to a different medium.
- Keep both controls editable. If the user changes the medium, show a reminder
  to verify the date; do not automatically clear or replace their values.
- Preserve dates as YYYY or YYYY-MM-DD, following the existing contract. Do not
  invent a month/day or substitute the work's first publication date.
- Prefer matching-book Next.js edition metadata, with matching-book JSON-LD as
  fallback. Use Open Graph only for title/cover fallback.
- Warn when a date comes from JSON-LD and its edition specificity is uncertain.
- Unknown formats remain unselected. Do not infer Audiobook from the user's
  library, previous entries, or the fact that ReadingView tracks audiobooks.
- Store the remote cover URL using current behavior. No automatic cover download
  or new image proxy is required; manual cover upload remains available.

### GR-004: Existing-entry warning

- Compare canonical Goodreads book IDs in existing `link_url` values, ignoring
  slug, query parameters, and fragments. Include archived/released/owned entries.
- Show matching entries with title, medium, status, and archive state. Distinguish
  the same medium from another medium; allow the user to continue with a new draft.
- Provide View existing, revealing the relevant filters and focusing the matching
  entry in the current page. Do not silently unarchive or change its status.
- Never overwrite an existing entry through the import flow.
- The current save endpoint still rejects exact duplicates with HTTP 409.
- Detection is best effort using stored links. Entries with a removed/replaced
  Goodreads link or a different Goodreads edition ID may not match. Cross-edition
  or title-similarity matching is outside this version.

### GR-005: Failure and draft preservation

- Invalid URL: explain the accepted Goodreads book-link format before fetching.
- Bot challenge, timeout, network failure, or unusable metadata: show an actionable
  inline message with Retry and a manual-entry option. Retain the supplied link.
- A successful partial result can still open an editable draft if it has a usable
  book title. Do not present a challenge/error page's title as book metadata.
- When moving to manual entry after failure, prefill the source link only.
- Retrying or receiving a late response must not overwrite user edits or reopen
  a dismissed editor. Ignore canceled/stale responses and do not retry silently.
- A save failure preserves the draft, including user corrections.

## Implementation design

### Backend

1. Extract reusable fetch/parser behavior from the prototype into a typed
   `backend/app/services/goodreads.py` service. Keep the CLI as a diagnostic
   wrapper over the same implementation, avoiding divergent parser copies.
2. Harden malformed metadata handling and book identity selection. Treat all
   remote HTML/JSON as untrusted data; never execute its scripts or render it.
3. Add request/response models in `backend/app/schemas/releases.py` and a thin
   `POST /api/releases/manual/lookup-goodreads` route in the releases router.
4. Request body: `{ "url": "https://www.goodreads.com/book/show/..." }`.
5. A successful response contains an editable draft compatible with the existing
   create contract, canonical source URL, per-field sources, missing fields,
   warnings, and matching existing-entry summaries. Use `media: []` for unknown
   media rather than the prototype's null. Do not return raw HTML or cookies.
6. Query source-link matches locally, including archived entries, without a DB
   write or a transaction held open during the external fetch.
7. Return useful string error details through the existing API error handling:
   422 for invalid input; 504 for upstream timeout; 502 for blocked access,
   upstream/network failure, oversized responses, or unusable metadata. A
   Goodreads 403 must not appear as a ReadingView authentication failure.
8. Reuse HTTPS Goodreads-host/book-path validation, bounded redirects with the
   same book ID, 5 MiB decoded-body limit, and request timeouts. Add a bounded
   overall lookup deadline. Do not send ABS/settings credentials or include
   raw upstream exception messages in responses/logs.
9. Keep parsing/fetching local to the ReadingView backend. No proxy service,
   Goodreads account/session, browser automation, LLM, or additional service.

No model, migration, scheduler, WebSocket event, or new configuration is planned.
The existing `link_url` stores the canonical Goodreads link. Source diagnostics
are transient and are not persisted. Standard create behavior sets the checked
timestamp when the reviewed record is saved.

### Frontend and contract

1. Add the lookup call to `frontend/src/lib/api.ts`, using the shared API helper
   and generated request/response types.
2. Add a lookup mutation in `frontend/src/hooks/useReleases.ts`. Lookup does not
   invalidate release queries; successful save retains existing invalidations.
3. Extend `ManualTrackingTab` and `ManualReleaseEditor` in
   `frontend/src/pages/ReleasesPage.tsx` with creation mode, draft initialization,
   source/warning presentation, and existing-entry navigation. Extract small
   components if that keeps lookup state separate from the editor's save state.
4. Keep local edits authoritative once the draft opens. Use existing shared UI
   components, theme tokens, accessible labels, and keyboard interactions.
5. Regenerate OpenAPI types using Python 3.12 and the exact repository export
   procedure. Inspect the generated diff; never hand-edit generated files.

## Delivery sequence

- [x] 1. Promote the probe to a typed reusable service and retain CLI parity.
- [x] 2. Add the lookup schema, route, and existing-entry lookup; regenerate types.
- [x] 3. Add the Goodreads creation path, editable draft, and error recovery.
- [x] 4. Add source-link warnings and navigation to existing entries.
- [x] 5. Complete focused automated checks and local UI verification.
- [ ] 6. When running in the intended deployment environment, repeat a read-only
      lookup to establish access there. Saving to production requires a separate
      user request; the feature work does not imply deployment authorization.

Step 1 verification: 42 focused service/CLI tests passed on Python 3.12, alongside
Ruff lint/format checks and strict mypy checks for both service modules. The
service defines typed fields, sources, lookup outcomes, and diagnostics; the CLI
retains its command, report format, and exit codes. Malformed nested metadata
is handled without inventing author, series number, or edition fields. No live
network request, API/schema change, or production change was made for this step.

Step 2 adds `POST /api/releases/manual/lookup-goodreads` with a `{ "url": "..." }`
body. The response includes `status`, `source_url`, `draft`, `sources`,
`missing_fields`, `warnings`, and `existing_releases`. The draft omits checked
timestamps/comments so saving it through the existing create contract applies
normal creation defaults. Lookup writes nothing and searches all saved source
links, including archived and released/owned entries, after the fetch completes.
The orchestration service is `backend/app/services/goodreads_import.py`; the
standalone parser/CLI remains independent of application settings and databases.

Step 2 verification: 373 backend tests passed with 83.91% coverage, including
17 lookup API/service tests. Backend Ruff lint/format checks and mypy passed.
The OpenAPI types were regenerated using Python 3.12; the diff contains only the
new endpoint and its four schema models. Frontend lint, formatting, type checks,
five tests, and build passed. Frontend checks ran on local Node 25.9.0, which
emits the existing Node 24 engine warning; CI's Node 24 runtime was not reproduced.
SQLite migration setup stalled in the execution sandbox, so the database tests
were rerun successfully outside it with temporary databases and mocked upstream
requests. No production calls or changes were made.

Step 3 adds the Manual / From Goodreads choice under Add release. The new
`frontend/src/components/releases/ReleaseCreation.tsx` component owns URL lookup,
review, manual fallback, and cancellation. The existing editor was extracted to
`ManualReleaseEditor.tsx` so imports, blank manual entries, and existing-row edits
share the same save/upload behavior. Imported values initialize local editable
state once, with source/warning presentation and an edition-date reminder.
Lookup uses generated contract types, the shared API helper, and a mutation with
automatic retries disabled. Abort signals and request identity checks prevent
late results from replacing manual edits or reopening canceled creation.

Step 3 verification: all 14 frontend tests passed, including nine new flow tests
covering manual creation, prefill/correction/save, partial results, invalid URLs,
retry, manual fallback, failed-save preservation, and late-response handling.
Lint, formatting, type checks, and build passed on the local Node 25.9.0 runtime
with the previously noted Node 24 engine warning. No backend source or contract
changed for this step, so backend tests and type generation were not repeated.
Browser verification against a running instance remains part of step 5. No
production request or data change was made. Existing-entry warnings/navigation
are intentionally still the next delivery item (step 4).

Step 4 displays all source-link matches returned by the lookup, with title,
author, available release date, medium, status, and archive state. Medium
comparison follows edits to the draft's selected media. The warning remains
advisory and the existing save-time duplicate rule is unchanged.

View existing enables the relevant list filters, loads archived entries when
needed, and focuses, scrolls to, and highlights the selected row. Already enabled
filters stay enabled. Repeated navigation refocuses the row; missing entries or
load failures produce a message with a retry path. The import editor and its
local edits remain mounted throughout navigation. Viewing a match never changes
its status, archive state, or stored fields.

Step 4 verification: all 24 frontend tests passed, including ten new cases for
multiple matches, unknown media, live medium comparisons, active/owned/released/
archived navigation, filter preservation, repeated focus, unavailable entries,
load-error recovery, and saving a different medium. Frontend lint, formatting,
type checks, and build passed on local Node 25.9.0 with the previously noted
Node 24 engine warning. No backend source/contract or production data changed.
Full browser verification remains in step 5.

Step 5 is complete. The final checks and browser acceptance matrix are recorded
in [goodreads-verification.md](goodreads-verification.md). The full backend suite
passed again (373 tests, 83.91% coverage), as did all 24 frontend tests, lint,
formatting, type checks, build, Bandit, and Python 3.12 OpenAPI regeneration parity.
Bandit identified the prototype's assertion in URL validation; validation now
uses the checked regex capture directly, and the suite was rerun after the fix.
Desktop/mobile Chromium verification used the built SPA, actual FastAPI routes,
Alembic-migrated temporary SQLite storage, and simulated Goodreads HTTP responses.
No production data or live Goodreads page was accessed during these checks.

## Acceptance and verification

| Scenario | Required result |
| --- | --- |
| User's Towering example | Draft matches the supplied report, including Ebook and 2027-08-17; no save before confirmation |
| Manual addition | Existing blank-form flow and save behavior remain usable |
| Partial/standalone metadata | Available fields populate; absent fields remain editable and blank |
| Change Ebook to Audiobook | Date stays editable with an edition reminder; no invented audiobook date |
| Same Goodreads ID | Warning includes hidden/archived matches; View existing reveals the selected entry |
| Different medium | Can save through the existing create endpoint |
| Exact existing duplicate | Existing 409 is shown without losing the draft |
| Bot challenge, including HTTP 202 | Useful failure message; no challenge title imported; retry/manual fallback available |
| Redirect outside Goodreads or to another book | Not followed; no request to local/private endpoints |
| Wrong-book or malformed metadata | No recommended-book import, unhandled parser error, or invalid draft values |
| Cancel, retry, late response, save failure | No accidental write or replacement of user edits |

Backend tests should cover parser selection and field mapping, malformed shapes,
date/format uncertainty, access failures and request bounds, source-link matching,
typed route responses, and zero writes during lookup. Reuse/extend the prototype
tests with mocked HTTP. Do not make live Goodreads access a CI dependency.

Add focused Vitest/Testing Library coverage for the two creation paths, editable
prefill, partial/error recovery, existing-entry navigation, and preservation of
edits across async state changes. Check source-link comparisons with tracked,
released/owned, and archived entries.

Run focused tests first, then the repository's non-mutating backend lint/format
checks, mypy, frontend lint/type checks/tests/build, and the backend suite with
the existing coverage gate. Verify generated OpenAPI parity on Python 3.12.
Record any checks that cannot run and why. Inspect git status before/after and
preserve the existing prototype files and unrelated changes.

## Deferred work and remaining risks

Refresh actions, scheduled scraping, change notifications, batch imports,
edition discovery, audiobook-date enrichment, Goodreads login, and persistent
source history are outside this version.

Goodreads access and embedded structures may change. Fallback is manual entry;
this version does not promise extraction from every book URL. A sanitized live
metadata fixture would improve confidence beyond the current synthetic cases,
but do not commit a full page containing unrelated account/review content.
There are no remaining product-scope questions after the three user decisions
above. Implementation may resolve routine component and schema naming choices.
