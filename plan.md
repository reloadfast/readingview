# Post-release enhancements

## Release calendar export

Provide an optional iCalendar (`.ics`) export/feed containing tracked and manually entered upcoming releases. It should work entirely locally, respect hidden/archived release states, include meaningful titles, dates, authors, series information and relevant links, and require no cloud calendar integration. Add focused API tests and a simple Releases-page entry point for downloading or copying the feed URL.

## Installable mobile experience (PWA)

Make the responsive SPA installable on phones and tablets using a web app manifest, application icons, and a service worker that caches only the app shell/static assets. Live library and personal data should continue to be fetched from the local server when online; do not persist sensitive API responses for offline use. Include an offline fallback state and verify the existing FastAPI SPA routing and production Docker build continue to work.
