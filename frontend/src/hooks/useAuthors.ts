import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  followAuthor,
  getAuthorDetail,
  getAuthors,
  getLibraryAuthors,
  searchAuthors,
  unfollowAuthor,
  type FollowRequest,
} from "../lib/api";

export function useAuthors() {
  return useQuery({
    queryKey: ["authors"],
    queryFn: getAuthors,
  });
}

export function useLibraryAuthors() {
  return useQuery({
    queryKey: ["authors", "library"],
    queryFn: getLibraryAuthors,
  });
}

export function useAuthorDetail(name: string) {
  return useQuery({
    queryKey: ["authors", "detail", name],
    queryFn: () => getAuthorDetail(name),
    enabled: Boolean(name),
  });
}

export function useSearchAuthors(q: string) {
  return useQuery({
    queryKey: ["authors", "search", q],
    queryFn: () => searchAuthors(q),
    enabled: q.length > 0,
  });
}

export function useFollowAuthor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FollowRequest) => followAuthor(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}

export function useUnfollowAuthor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (olKey: string) => unfollowAuthor(olKey),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}
