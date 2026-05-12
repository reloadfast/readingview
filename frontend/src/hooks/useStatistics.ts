import { useQuery } from "@tanstack/react-query";
import { getHeatmap, getRecap, getStatistics, getYearlyStats } from "../lib/api";

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
