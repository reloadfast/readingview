import { useQuery } from "@tanstack/react-query";
import { getSeries, getSeriesDetail } from "../lib/api";

export function useSeries() {
  return useQuery({
    queryKey: ["series"],
    queryFn: getSeries,
  });
}

export function useSeriesDetail(name: string) {
  return useQuery({
    queryKey: ["series", name],
    queryFn: () => getSeriesDetail(name),
    enabled: Boolean(name),
  });
}
