// GENERATED schema types — extracted from the OpenAPI spec at build time.
// Do not edit manually — run `pnpm openapi` to regenerate.

import type { components } from "./api.generated";

export type ABSTestRequest = components["schemas"]["ABSTestRequest"];
export type AddItemRequest = components["schemas"]["AddItemRequest"];
export type AuthorCount = components["schemas"]["AuthorCount"];
export type BookProgress = components["schemas"]["BookProgress"];
export type BookSummary = components["schemas"]["BookSummary"];
export type CollectionDetail = components["schemas"]["CollectionDetail"];
export type CollectionOut = components["schemas"]["CollectionOut"];
export type CreateCollectionRequest = components["schemas"]["CreateCollectionRequest"];
export type FollowRequest = components["schemas"]["FollowRequest"];
export type GenreCount = components["schemas"]["GenreCount"];
export type HeatmapData = components["schemas"]["HeatmapData"];
export type HeatmapPoint = components["schemas"]["HeatmapPoint"];
export type HTTPValidationError = components["schemas"]["HTTPValidationError"];
export type IngestRequest = components["schemas"]["IngestRequest"];
export type IngestResponse = components["schemas"]["IngestResponse"];
export type LLMTestRequest = components["schemas"]["LLMTestRequest"];
export type LibraryAuthor = components["schemas"]["LibraryAuthor"];
export type LibraryBook = components["schemas"]["LibraryBook"];
export type MonthlyPoint = components["schemas"]["MonthlyPoint"];
export type NarratorBook = components["schemas"]["NarratorBook"];
export type NarratorDetail = components["schemas"]["NarratorDetail"];
export type NarratorSummary = components["schemas"]["NarratorSummary"];
export type NoteOut = components["schemas"]["NoteOut"];
export type NotePut = components["schemas"]["NotePut"];
export type OLAuthorResult = components["schemas"]["OLAuthorResult"];
export type OverallStats = components["schemas"]["OverallStats"];
export type PatchCollectionRequest = components["schemas"]["PatchCollectionRequest"];
export type PatchReleaseRequest = components["schemas"]["PatchReleaseRequest"];
export type ReadDuration = components["schemas"]["ReadDuration"];
export type ReadingGoalOut = components["schemas"]["ReadingGoalOut"];
export type ReadingGoalRequest = components["schemas"]["ReadingGoalRequest"];
export type RecapStats = components["schemas"]["RecapStats"];
export type RefreshError = components["schemas"]["RefreshError"];
export type RefreshResult = components["schemas"]["RefreshResult"];
export type ReleaseOut = components["schemas"]["ReleaseOut"];
export type ReleaseTrackedAuthorOut = components["schemas"]["ReleaseTrackedAuthorOut"];
export type SeriesBook = components["schemas"]["SeriesBook"];
export type SeriesDetail = components["schemas"]["SeriesDetail"];
export type SeriesEntry = components["schemas"]["SeriesEntry"];
export type SeriesSummary = components["schemas"]["SeriesSummary"];
export type SettingsPatch = components["schemas"]["SettingsPatch"];
export type SettingsRead = components["schemas"]["SettingsRead"];
export type StatusResponse = components["schemas"]["StatusResponse"];
export type StreakInfo = components["schemas"]["StreakInfo"];
export type TestConnectionResponse = components["schemas"]["TestConnectionResponse"];
export type TrackAuthorRequest = components["schemas"]["TrackAuthorRequest"];
export type TrackedAuthorOut = components["schemas"]["TrackedAuthorOut"];
export type ValidationError = components["schemas"]["ValidationError"];
export type YearlyPoint = components["schemas"]["YearlyPoint"];
export type YearlyStats = components["schemas"]["YearlyStats"];

export interface AuthorBook {
  id: string;
  title: string;
  narrator: string;
  duration: number;
  duration_formatted: string;
  is_finished: boolean;
}

export interface AuthorDetail {
  name: string;
  book_count: number;
  total_hours: number;
  finished_count: number;
  books: AuthorBook[];
}
