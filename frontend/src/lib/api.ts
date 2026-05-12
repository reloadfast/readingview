// ---------------------------------------------------------------------------
// Schema types — generated from backend OpenAPI spec
// ---------------------------------------------------------------------------

import type {
  AddItemRequest,
  ABSTestRequest,
  CollectionDetail,
  CollectionOut,
  CreateCollectionRequest,
  FollowRequest,
  HeatmapData,
  IngestRequest,
  IngestResponse,
  LLMTestRequest,
  LibraryAuthor,
  LibraryBook,
  NoteOut,
  OverallStats,
  PatchCollectionRequest,
  ReleaseOut,
  ReleaseTrackedAuthorOut,
  SettingsPatch,
  SettingsRead,
  TestConnectionResponse,
  TrackAuthorRequest,
  TrackedAuthorOut,
  YearlyStats,
  RecapStats,
  SeriesSummary,
  SeriesDetail,
  NarratorSummary,
  NarratorDetail,
  OLAuthorResult,
  RefreshResult,
  PatchReleaseRequest,
} from "./api.schemas";

export type {
  AddItemRequest,
  ABSTestRequest,
  AuthorCount,
  BookProgress,
  BookSummary,
  CollectionDetail,
  CollectionOut,
  CreateCollectionRequest,
  FollowRequest,
  GenreCount,
  HeatmapData,
  HeatmapPoint,
  IngestRequest,
  IngestResponse,
  LLMTestRequest,
  LibraryAuthor,
  LibraryBook,
  MonthlyPoint,
  NarratorBook,
  NarratorDetail,
  NarratorSummary,
  NoteOut,
  NotePut,
  OLAuthorResult,
  OverallStats,
  PatchCollectionRequest,
  PatchReleaseRequest,
  ReadDuration,
  ReadingGoalOut,
  ReadingGoalRequest,
  RecapStats,
  RefreshError,
  RefreshResult,
  ReleaseOut,
  ReleaseTrackedAuthorOut,
  SeriesBook,
  SeriesDetail,
  SeriesEntry,
  SeriesSummary,
  SettingsPatch,
  SettingsRead,
  StatusResponse,
  StreakInfo,
  TestConnectionResponse,
  TrackAuthorRequest,
  TrackedAuthorOut,
  YearlyPoint,
  YearlyStats,
} from "./api.schemas";

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

export function getHeatmap(year: string): Promise<HeatmapData> {
  return apiFetch(`/statistics/heatmap?year=${encodeURIComponent(year)}`);
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

export interface Recommendation {
  book_id: string;
  title: string;
  authors: string[];
  description: string | null;
  subjects: string[];
  cover_id: number | null;
  work_key: string | null;
  score: number;
  explanation: string | null;
  feedback: number;
}

export interface RecommenderStatus {
  enabled: boolean;
  model: string | null;
  vector_backend: string | null;
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

export function submitFeedback(bookId: string, vote: 1 | -1): Promise<void> {
  return apiFetch(`/recommendations/${encodeURIComponent(bookId)}/feedback`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  });
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
// Notes
// ---------------------------------------------------------------------------


export function getNote(absItemId: string): Promise<NoteOut> {
  return apiFetch(`/notes/${encodeURIComponent(absItemId)}`);
}

export function upsertNote(absItemId: string, body: string): Promise<NoteOut> {
  return apiFetch(`/notes/${encodeURIComponent(absItemId)}`, {
    method: "PUT",
    body: JSON.stringify({ body }),
  });
}

export function deleteNote(absItemId: string): Promise<void> {
  return apiFetch(`/notes/${encodeURIComponent(absItemId)}`, { method: "DELETE" });
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
