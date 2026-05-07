import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addTrackedAuthor,
  getReleases,
  getTrackedAuthors,
  refreshReleases,
  removeTrackedAuthor,
  type TrackAuthorRequest,
} from "../lib/api";

export function useReleases(author?: string) {
  return useQuery({
    queryKey: ["releases", author ?? null],
    queryFn: () => getReleases(author),
  });
}

export function useTrackedAuthors() {
  return useQuery({
    queryKey: ["releases", "tracked-authors"],
    queryFn: getTrackedAuthors,
  });
}

export function useAddTrackedAuthor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TrackAuthorRequest) => addTrackedAuthor(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["releases"] });
    },
  });
}

export function useRemoveTrackedAuthor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => removeTrackedAuthor(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["releases"] });
    },
  });
}

export function useRefreshReleases() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: refreshReleases,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["releases"] });
    },
  });
}
