# Goodreads access and parsing prototype

This read-only CLI checks whether the machine running it can access a public
Goodreads book page and extract fields for an existing manual release. It does
not start the app, connect to ABS, write to the database, or save anything.
It uses the backend's existing `httpx` dependency and Python's HTML parser.

Fetch/parsing logic and typed result definitions now live in
`backend/app/services/goodreads.py`. The CLI module is a wrapper over that service;
its invocation, JSON report format, and exit codes remain the same.

From the repository root, using the existing backend environment:

```bash
cd backend
.venv/bin/python -m app.services.goodreads_probe \
  'https://www.goodreads.com/book/show/257149406-bog-standard-isekai'
```

Run the same command from a checkout on the ReadingView host to assess access
from that host's network. No Goodreads login, cookie, API key, proxy service,
browser automation, or application configuration is required.

To inspect parsing independently of network access, save the book page's HTML
locally and pass its path (not a screenshot):

```bash
.venv/bin/python -m app.services.goodreads_probe \
  'https://www.goodreads.com/book/show/257149406-bog-standard-isekai' \
  --html /tmp/goodreads-book.html
```

The JSON report includes extracted `fields`, per-field `sources`, missing fields,
warnings, and (for live requests) HTTP status and received byte count. It does
not print response HTML, headers, cookies, or network exception messages.

- `ok`: all seven metadata fields were extracted; still review them.
- `partial`: a title was found, but some metadata is missing.
- `blocked`: bot verification, HTTP 403/429, or a disallowed/looping redirect.
- `no_metadata`: no usable title and no recognized bot-verification marker.
- `http_error`, `network_error`, `too_large`: the access check failed.

Exit codes: 0 for `ok`/`partial`, 1 for access or metadata failure, 2 for invalid
CLI input. A network failure does not establish that Goodreads blocked access.

The parser attempts matching-book Next.js/Apollo data, JSON-LD Book metadata,
then Open Graph title/cover fallbacks. Next.js edition dates take precedence;
JSON-LD dates carry a warning because they may describe the work. It never
substitutes a work's original publication date for missing edition metadata or
infers an audiobook date from an ebook date. Unknown formats/dates stay empty.
Status defaults to `watching`; comments remain user-authored in a future form.

The parser is deliberately experimental: the Next.js shape is based on expected
Goodreads structures, not a verified capture of the example page. Tests use
synthetic fixtures. Live HTML may require parser adjustments. No continuous
monitoring, application API/UI integration, or database migration is included.

Live check on 2026-11-05 from the development execution environment: the example
book ID returned HTTP 202 with a 2,443-byte bot-verification page and no detected
JSON-LD or Next.js metadata. The probe reported `blocked` with all metadata fields
empty. This confirms an access obstacle from that environment, not from the
ReadingView production host, which has not been tested. A successful live page
capture is still needed to validate the parser against Goodreads' actual data.

Follow-up on 2026-11-05: the user ran the probe on Fijo and received HTTP 200,
159,588 bytes, and `status: ok`. All seven metadata fields were extracted for
Towering, including series number 6, Ebook format, and release date 2027-08-17.
The date came from Next.js metadata; the medium came from JSON-LD. This validates
access and extraction for that page from Fijo. Access from the deployed
ReadingView container and broader page coverage remain unverified. The scoped
feature plan is recorded in [goodreads-import-plan.md](goodreads-import-plan.md).

Requests accept only HTTPS Goodreads book URLs, check every redirect, keep the
same book ID, time out after 20 seconds per request, and limit decoded responses
to 5 MiB. Saved HTML uses the same size limit. No bot protection is bypassed.

Focused verification from the repository root:

```bash
cd backend
.venv/bin/pytest tests/test_goodreads.py tests/test_goodreads_probe.py --no-cov
```
