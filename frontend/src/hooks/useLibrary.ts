import { useQuery } from "@tanstack/react-query";
import { getBook, getInProgress, getLibrary, type LibraryParams } from "../lib/api";

export function useLibrary(params?: LibraryParams) {
  return useQuery({
    queryKey: ["library", params],
    queryFn: () => getLibrary(params),
  });
}

export function useInProgress() {
  return useQuery({
    queryKey: ["library", "in-progress"],
    queryFn: getInProgress,
  });
}

export function useBook(id: string) {
  return useQuery({
    queryKey: ["library", id],
    queryFn: () => getBook(id),
    enabled: Boolean(id),
  });
}
