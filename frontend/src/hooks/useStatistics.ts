import { useQuery } from "@tanstack/react-query";
import { getAuthorNarratorAffinity, getBacklogHealth, getBookLengthPreferences, getCompletionVelocity, getDurationCompletionCorrelation, getExtraListening, getGenreCompletionCorrelation, getGoalForecast, getHeatmap, getListeningHabits, getMonthlyComparison, getRecap, getSeriesProgress, getStatistics, getStatisticsDetail, getYearlyStats } from "../lib/api";

export function useStatistics() {
  return useQuery({
    queryKey: ["statistics"],
    queryFn: getStatistics,
  });
}

export function useYearlyStats(year: string) {
  return useQuery({
    queryKey: ["statistics", "yearly", year],
    queryFn: () => getYearlyStats(year),
    enabled: Boolean(year),
  });
}

export function useRecap(year: string) {
  return useQuery({
    queryKey: ["statistics", "recap", year],
    queryFn: () => getRecap(year),
    enabled: Boolean(year),
  });
}

export function useHeatmap(year: string) {
  return useQuery({
    queryKey: ["statistics", "heatmap", year],
    queryFn: () => getHeatmap(year),
    enabled: Boolean(year),
  });
}

export function useListeningHabits(year: string) {
  return useQuery({
    queryKey: ["statistics", "habits", year],
    queryFn: () => getListeningHabits(year),
    enabled: Boolean(year),
  });
}

export function useCompletionVelocity(year: string) {
  return useQuery({
    queryKey: ["statistics", "completion-velocity", year],
    queryFn: () => getCompletionVelocity(year),
    enabled: Boolean(year),
  });
}

export function useMonthlyComparison(year: string) {
  return useQuery({
    queryKey: ["statistics", "monthly-comparison", year],
    queryFn: () => getMonthlyComparison(year),
    enabled: Boolean(year),
  });
}

export function useBookLengthPreferences(year: string) {
  return useQuery({
    queryKey: ["statistics", "book-length-preferences", year],
    queryFn: () => getBookLengthPreferences(year),
    enabled: Boolean(year),
  });
}

export function useGoalForecast(year: string) {
  return useQuery({
    queryKey: ["statistics", "goal-forecast", year],
    queryFn: () => getGoalForecast(year),
    enabled: Boolean(year),
  });
}

export function useBacklogHealth() {
  return useQuery({
    queryKey: ["statistics", "backlog-health"],
    queryFn: getBacklogHealth,
  });
}

export function useSeriesProgress() {
  return useQuery({
    queryKey: ["statistics", "series-progress"],
    queryFn: getSeriesProgress,
  });
}

export function useAuthorNarratorAffinity() {
  return useQuery({
    queryKey: ["statistics", "affinity"],
    queryFn: getAuthorNarratorAffinity,
  });
}

export function useGenreCompletionCorrelation() {
  return useQuery({
    queryKey: ["statistics", "genre-completion"],
    queryFn: getGenreCompletionCorrelation,
  });
}

export function useDurationCompletionCorrelation(year: string) {
  return useQuery({
    queryKey: ["statistics", "duration-completion", year],
    queryFn: () => getDurationCompletionCorrelation(year),
    enabled: Boolean(year),
  });
}

export function useExtraListening(year: string) {
  return useQuery({
    queryKey: ["statistics", "extra-listening", year],
    queryFn: () => getExtraListening(year),
    enabled: Boolean(year),
  });
}

export function useStatisticsDetail(year: string) {
  return useQuery({
    queryKey: ["statistics", "detail", year],
    queryFn: () => getStatisticsDetail(year),
    enabled: Boolean(year),
  });
}
