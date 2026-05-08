// ---------------------------------------------------------------------------
// Types — mirror Pydantic schemas exactly
// ---------------------------------------------------------------------------

export interface SeriesEntry {
  name: string;
  sequence: string | null;
}

export interface BookProgress {
  is_finished: boolean;
  progress_pct: number;
  current_time: number;
  time_remaining: number;
  started_at: number | null;
  finished_at: number | null;
  last_update: number | null;
}

export interface LibraryBook {
  id: string;
  title: string;
  authors: string;
  narrator: string | null;
  series: SeriesEntry[];
  cover_url: string;
  duration: number;
  genres: string[];
  description: string | null;
  published_year: string | null;
  isbn: string | null;
  asin: string | null;
  progress: BookProgress | null;
}

export interface StreakInfo {
  current: number;
  longest: number;
  total_days: number;
}

export interface YearlyPoint {
  year: string;
  books: number;
}

export interface OverallStats {
  books_completed: number;
  hours_listened: number;
  avg_books_per_month: number;
  unique_authors: number;
  streak: StreakInfo;
  by_year: YearlyPoint[];
}

export interface MonthlyPoint {
  month: string;
  books: number;
}

export interface AuthorCount {
  name: string;
  books: number;
}

export interface GenreCount {
  name: string;
  books: number;
}

export interface YearlyStats {
  year: string;
  books_in_year: number;
  monthly_chart: MonthlyPoint[];
  top_authors: AuthorCount[];
  top_narrators: AuthorCount[];
  genre_breakdown: GenreCount[];
}

export interface BookSummary {
  id: string;
  title: string;
  author: string;
  duration: number;
}

export interface ReadDuration {
  id: string;
  title: string;
  days: number;
}

export interface RecapStats {
  year: string;
  books_finished: number;
  hours_listened: number;
  hours_of_content: number;
  active_months: number;
  top_authors: AuthorCount[];
  longest_book: BookSummary | null;
  shortest_book: BookSummary | null;
  fastest_read: ReadDuration | null;
  slowest_read: ReadDuration | null;
  monthly_pace: MonthlyPoint[];
  top_series: GenreCount[];
}

export interface TrackedAuthorOut {
  id: number;
  name: string;
  ol_key: string | null;
  photo_url: string | null;
  bio: string | null;
  birth_date: string | null;
  death_date: string | null;
  followed_at: number;
}

export interface LibraryAuthor {
  name: string;
  book_count: number;
}

export interface OLAuthorResult {
  ol_key: string;
  name: string;
  birth_date: string | null;
  death_date: string | null;
  photo_url: string | null;
  top_work: string | null;
  work_count: number;
}

export interface FollowRequest {
  name: string;
  ol_key?: string | null;
}

export interface SeriesSummary {
  name: string;
  author: string;
  total: number;
  finished: number;
  in_progress: number;
  not_started: number;
  percent_complete: number;
}

export interface SeriesBook {
  id: string;
  title: string;
  author: string;
  sequence: string;
  is_finished: boolean;
  progress: number;
  duration: number;
  duration_formatted: string;
}

export interface SeriesDetail extends SeriesSummary {
  books: SeriesBook[];
}

export interface ReleaseTrackedAuthorOut {
  id: number;
  name: string;
  ol_key: string | null;
  added_at: number;
}

export interface TrackAuthorRequest {
  name: string;
  ol_key?: string | null;
}

export interface ReleaseOut {
  id: number;
  title: string;
  author_name: string;
  release_date: string | null;
  release_date_confirmed: boolean;
  book_number: string | null;
  ol_key: string | null;
  link_url: string | null;
  notes: string | null;
  source: string | null;
}

export interface RefreshError {
  author: string;
  message: string;
}

export interface RefreshResult {
  added: number;
  skipped: number;
  failed: number;
  errors: RefreshError[];
}

export interface NarratorBook {
  id: string;
  title: string;
  author: string;
  duration: number;
  duration_formatted: string;
  is_finished: boolean;
}

export interface NarratorSummary {
  name: string;
  book_count: number;
  total_hours: number;
  finished_count: number;
}

export interface NarratorDetail extends NarratorSummary {
  books: NarratorBook[];
}

export interface CollectionOut {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  book_count: number;
}

export interface CollectionDetail extends CollectionOut {
  item_ids: string[];
}

export interface CreateCollectionRequest {
  name: string;
  description?: string | null;
}

export interface PatchCollectionRequest {
  name?: string | null;
  description?: string | null;
}

export interface AddItemRequest {
  abs_item_id: string;
}

export interface SettingsRead {
  abs_url: string | null;
  abs_token: string | null;
  recommender_enabled: boolean;
  recommender_vector_backend: string;
  recommender_embed_model: string;
  recommender_top_k: number;
  recommender_min_similarity: number;
  recommender_explanations_enabled: boolean;
  llm_type: string;
  llm_endpoint: string | null;
  llm_model: string | null;
  llm_api_key: string | null;
  notifications_enabled: boolean;
  apprise_url: string | null;
  notify_days_before: number;
  notify_time: string;
  timezone: string;
}

export type SettingsPatch = Partial<Omit<SettingsRead, "abs_token" | "llm_api_key" | "apprise_url">> & {
  abs_token?: string | null;
  llm_api_key?: string | null;
  apprise_url?: string | null;
};

export interface LLMTestRequest {
  endpoint: string;
  llm_type?: string;
  api_key?: string | null;
}

export interface ABSTestRequest {
  url: string;
  token: string;
}

export interface TestConnectionResponse {
  ok: boolean;
  models: string[] | null;
  error: string | null;
  metadata: Record<string, unknown> | null;
}

export interface IngestRequest {
  isbn?: string | null;
  title?: string | null;
  author?: string | null;
  work_key?: string | null;
}

export interface IngestResponse {
  book_id: string;
}

export interface RecommenderStatus {
  enabled: boolean;
  model: string | null;
  vector_backend: string | null;
}

export interface Recommendation {
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Core fetch helper
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) message = String(body.detail);
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Library
// ---------------------------------------------------------------------------

export interface LibraryParams {
  search?: string;
  sort?: "title" | "progress_asc" | "progress_desc" | "updated" | "finished";
  page?: number;
  limit?: number;
}

export function getLibrary(params?: LibraryParams): Promise<LibraryBook[]> {
  const q = new URLSearchParams();
  if (params?.search) q.set("search", params.search);
  if (params?.sort) q.set("sort", params.sort);
  if (params?.page != null) q.set("page", String(params.page));
  if (params?.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiFetch(`/library${qs ? `?${qs}` : ""}`);
}

export function getInProgress(): Promise<LibraryBook[]> {
  return apiFetch("/library/in-progress");
}

export function getBook(id: string): Promise<LibraryBook> {
  return apiFetch(`/library/${encodeURIComponent(id)}`);
}

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------

export function getStatistics(): Promise<OverallStats> {
  return apiFetch("/statistics");
}

export function getYearlyStats(year: string): Promise<YearlyStats> {
  return apiFetch(`/statistics/yearly?year=${encodeURIComponent(year)}`);
}

export function getRecap(year: string): Promise<RecapStats> {
  return apiFetch(`/statistics/recap?year=${encodeURIComponent(year)}`);
}

// ---------------------------------------------------------------------------
// Authors
// ---------------------------------------------------------------------------

export function getAuthors(): Promise<TrackedAuthorOut[]> {
  return apiFetch("/authors");
}

export function getLibraryAuthors(): Promise<LibraryAuthor[]> {
  return apiFetch("/authors/library");
}

export function followAuthor(body: FollowRequest): Promise<TrackedAuthorOut> {
  return apiFetch("/authors", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function unfollowAuthor(olKey: string): Promise<void> {
  return apiFetch(`/authors/${encodeURIComponent(olKey)}`, { method: "DELETE" });
}

export function searchAuthors(q: string): Promise<OLAuthorResult[]> {
  return apiFetch(`/authors/search?q=${encodeURIComponent(q)}`);
}

// ---------------------------------------------------------------------------
// Series
// ---------------------------------------------------------------------------

export function getSeries(): Promise<SeriesSummary[]> {
  return apiFetch("/series");
}

export function getSeriesDetail(name: string): Promise<SeriesDetail> {
  return apiFetch(`/series/${encodeURIComponent(name)}`);
}

// ---------------------------------------------------------------------------
// Releases
// ---------------------------------------------------------------------------

export function getReleases(author?: string): Promise<ReleaseOut[]> {
  const q = author ? `?author=${encodeURIComponent(author)}` : "";
  return apiFetch(`/releases${q}`);
}

export function getTrackedAuthors(): Promise<ReleaseTrackedAuthorOut[]> {
  return apiFetch("/releases/tracked-authors");
}

export function addTrackedAuthor(body: TrackAuthorRequest): Promise<ReleaseTrackedAuthorOut> {
  return apiFetch("/releases/tracked-authors", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function removeTrackedAuthor(id: number): Promise<void> {
  return apiFetch(`/releases/tracked-authors/${id}`, { method: "DELETE" });
}

export function refreshReleases(): Promise<RefreshResult> {
  return apiFetch("/releases/refresh", { method: "POST" });
}

export interface PatchReleaseRequest {
  release_date_confirmed?: boolean;
  release_date?: string | null;
  notes?: string | null;
}

export function patchRelease(id: number, body: PatchReleaseRequest): Promise<ReleaseOut> {
  return apiFetch(`/releases/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}

// ---------------------------------------------------------------------------
// Narrators
// ---------------------------------------------------------------------------

export function getNarrators(): Promise<NarratorSummary[]> {
  return apiFetch("/narrators");
}

export function getNarratorDetail(name: string): Promise<NarratorDetail> {
  return apiFetch(`/narrators/${encodeURIComponent(name)}`);
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

export function getCollections(): Promise<CollectionOut[]> {
  return apiFetch("/collections");
}

export function getCollection(id: number): Promise<CollectionDetail> {
  return apiFetch(`/collections/${id}`);
}

export function createCollection(body: CreateCollectionRequest): Promise<CollectionOut> {
  return apiFetch("/collections", { method: "POST", body: JSON.stringify(body) });
}

export function updateCollection(id: number, body: PatchCollectionRequest): Promise<CollectionOut> {
  return apiFetch(`/collections/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function deleteCollection(id: number): Promise<void> {
  return apiFetch(`/collections/${id}`, { method: "DELETE" });
}

export function addToCollection(id: number, absItemId: string): Promise<CollectionDetail> {
  return apiFetch(`/collections/${id}/items`, {
    method: "POST",
    body: JSON.stringify({ abs_item_id: absItemId } satisfies AddItemRequest),
  });
}

export function removeFromCollection(id: number, itemId: string): Promise<void> {
  return apiFetch(`/collections/${id}/items/${encodeURIComponent(itemId)}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export function getSettings(): Promise<SettingsRead> {
  return apiFetch("/settings");
}

export function updateSettings(body: SettingsPatch): Promise<SettingsRead> {
  return apiFetch("/settings", { method: "PATCH", body: JSON.stringify(body) });
}

// ---------------------------------------------------------------------------
// Connections
// ---------------------------------------------------------------------------

export function testLlmConnection(body: LLMTestRequest): Promise<TestConnectionResponse> {
  return apiFetch("/llm/test-connection", { method: "POST", body: JSON.stringify(body) });
}

export function testAbsConnection(body: ABSTestRequest): Promise<TestConnectionResponse> {
  return apiFetch("/abs/test-connection", { method: "POST", body: JSON.stringify(body) });
}

// ---------------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------------

export interface RecommendationParams {
  book_ids?: string[];
  prompt?: string;
}

export function getRecommendations(params?: RecommendationParams): Promise<Recommendation[]> {
  const q = new URLSearchParams();
  if (params?.book_ids?.length) q.set("book_ids", params.book_ids.join(","));
  if (params?.prompt) q.set("prompt", params.prompt);
  const qs = q.toString();
  return apiFetch(`/recommendations${qs ? `?${qs}` : ""}`);
}

export function ingestBook(body: IngestRequest): Promise<IngestResponse> {
  return apiFetch("/recommendations/ingest", { method: "POST", body: JSON.stringify(body) });
}

export function getRecommenderStatus(): Promise<RecommenderStatus> {
  return apiFetch("/recommendations/status");
}

// ---------------------------------------------------------------------------
// Goals
// ---------------------------------------------------------------------------

export interface ReadingGoal {
  year: number;
  target_books: number;
}

export function getGoals(): Promise<ReadingGoal[]> {
  return apiFetch("/goals");
}

export function setGoal(year: number, target_books: number): Promise<ReadingGoal> {
  return apiFetch(`/goals/${year}`, {
    method: "PUT",
    body: JSON.stringify({ target_books }),
  });
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch("/health");
}

// ---------------------------------------------------------------------------
// Backup
// ---------------------------------------------------------------------------

export async function downloadBackup(): Promise<Blob> {
  const res = await fetch("/api/backup");
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  return res.blob();
}

export async function uploadRestore(file: File): Promise<{ status: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/restore", { method: "POST", body: form });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) message = String(body.detail);
    } catch {
      // ignore
    }
    throw new ApiError(res.status, message);
  }
  return res.json();
}
