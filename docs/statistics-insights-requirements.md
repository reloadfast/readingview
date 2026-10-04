# Statistics Insights Requirements

## Purpose

Extend the Statistics page with actionable listening-habit, progress, and
preference insights. All calculations must remain local to the ReadingView
instance and use only Audiobookshelf (ABS) data already available to the
application plus ReadingView's existing reading goals.

## Scope and data rules

### R-001: Privacy and data sources

- The feature must not send listening history, library metadata, or derived
  insights to an external service.
- It must use ABS listening sessions, the media-progress map, library metadata,
  and ReadingView goals as its source data.
- A metric must omit records with missing or invalid input values rather than
  infer a value.

### R-002: Time handling

- Session timestamps must be converted using the server's configured local
  timezone before deriving a calendar date, weekday, or hour of day.
- A session's listening duration must be attributed to the date and hour of its
  session timestamp; the UI must label this convention where it affects an
  interpretation.
- Year-filtered views must include only data attributed to the selected year.

### R-003: Empty and partial data

- Each insight must render an explicit empty state when no qualifying data
  exists.
- Where a calculation uses only a subset of records, the UI must state the
  sample size or explain the eligibility criterion.
- Zero values and unavailable values must be visually distinguishable.

### R-004: Drill-down and accessibility

- Charts must have an equivalent textual summary for assistive technology.
- Where underlying sessions or books are available, selecting a visual datum
  must open the existing statistics detail view filtered to the relevant date,
  month, title, author, narrator, genre, or series.
- All new cards and charts must work with keyboard navigation and existing theme
  tokens.

## Listening habits

### R-101: Listening by weekday and hour

- The Statistics page must show a heatmap or equivalent matrix of total
  listening minutes grouped by weekday and local hour (0–23).
- The selected year must constrain the displayed sessions; the all-time view
  must include all available sessions.
- The UI must identify the highest-listening weekday/hour combination and allow
  users to inspect its total minutes and session count.

### R-102: Session-habit summary

- The Statistics page must display the average and median listening-session
  duration, sessions per active listening day, and longest recorded session for
  the selected period.
- It must show a distribution of session durations using the following bins:
  under 15 minutes, 15–29 minutes, 30–59 minutes, and 60 minutes or more.
- Sessions with zero or negative `timeListening` must not affect these metrics.

### R-103: Active listening cadence

- The Statistics page must show active listening days, total listening days in
  the selected period, and the percentage of days with listening activity.
- For a selected calendar year, the denominator must be all days in that year;
  for all-time, it must be the inclusive span between the first and latest
  qualifying listening day.

## Completion and pace

### R-201: Completion velocity

- For completed books with valid `startedAt` and `finishedAt` timestamps, the
  page must show median days to finish and a monthly trend of median completion
  time.
- The trend must not be rendered for a month with fewer than three qualifying
  completed books; it must expose that limitation in the chart summary.
- The existing fastest and slowest completion figures may remain, but must be
  presented as outliers rather than representative pace.

### R-202: Books and hours comparison

- The monthly breakdown must offer a switch between books completed and
  listening hours.
- The listening-hours view must aggregate session `timeListening`, not a
  completed book's full media duration.
- A concise comparison must call out whether a monthly change in completions is
  accompanied by a contrary change in listening hours.

### R-203: Book-length preference

- The page must show a distribution of completed-book media durations in these
  bins: under 5 hours, 5–9:59, 10–19:59, 20–29:59, and 30 hours or more.
- It must state the median completed-book duration for the selected period.
- A companion view must compare duration bucket with median days to finish,
  excluding titles without valid start and finish timestamps.

## Goals and backlog

### R-301: Goal forecast

- When a reading goal exists for the selected calendar year, the page must show
  projected books completed by year end based on the trailing 30-day completion
  pace.
- It must also show the required average books per remaining week to reach the
  goal.
- The projection must be labelled as an estimate and must not be shown when
  fewer than 14 days have elapsed in the selected year or no qualifying recent
  completion exists.

### R-302: Backlog health

- The page must display counts of unstarted, in-progress, and completed library
  books, plus total media hours remaining for unstarted and in-progress books.
- Remaining time for an in-progress book must use its ABS progress percentage
  when the duration and progress are valid; otherwise it must be omitted from
  the hours total.
- The UI must highlight the number of partially started books as a separate
  actionable value.

### R-303: Series progress

- The page must list series with incomplete books, including completed count,
  remaining count, and remaining media hours.
- It must provide a "closest to finish" ordering based on fewest remaining
  books, then fewest remaining hours.
- A series must be excluded when its books do not provide enough data to
  determine an incomplete count.

## Preferences and correlations

### R-401: Author and narrator affinity

- For authors and narrators with at least three library books, the page must
  show finished count, available-library count, completion rate, and listened
  hours.
- Multiple credited authors or narrators must count toward every credited
  person; the UI must disclose that totals may therefore exceed the number of
  books.
- Rankings must support sorting by completion rate, completed books, or
  listening hours, with an explicit default sort.

### R-402: Genre completion correlation

- For genres with at least three started or completed books, the page must show
  completion rate and median days to finish for qualifying completed books.
- A genre's completion rate must use books with a known progress record as its
  denominator.
- The UI must label this as an observed association, not evidence that genre
  causes a completion outcome.

### R-403: Duration and completion correlation

- The page must visualize completed-book duration against days to finish for
  titles with valid duration, start, and finish timestamps.
- It must provide a plain-language summary of the observed direction (positive,
  negative, or no clear relationship) only when at least ten qualifying books
  exist.
- Any correlation coefficient, if shown, must use a documented method and must
  be omitted when the data lacks meaningful variation.

### R-404: Re-listening and over-listening

- For completed books with a valid media duration, the page must calculate the
  listening ratio as total `timeListening` divided by duration.
- It must surface titles at or above 125% as "extra listening" rather than
  asserting that the user re-listened to them.
- The view must explain that playback restarts, seeking, and ABS session
  accounting can also increase this ratio.

## Delivery and quality

### R-501: API contract

- New insights must be exposed through typed FastAPI schemas and routes; the
  generated frontend OpenAPI types must be regenerated from the backend
  contract rather than hand-edited.
- Existing statistics endpoints must remain backward compatible unless a
  versioned replacement is introduced.

### R-502: Performance and failure handling

- Statistics calculations must reuse the existing cached ABS listening-stat and
  listening-session retrieval paths.
- A failure to retrieve a nonessential insight must display an inline error for
  that section without preventing existing statistics from rendering.

### R-503: Test coverage

- Backend tests must cover timezone/year boundaries, missing timestamps,
  zero-duration sessions, empty data, threshold sample sizes, and the numerical
  calculations for each insight.
- Frontend tests must cover empty, loading, error, and populated states, plus
  the goal projection eligibility rules.
