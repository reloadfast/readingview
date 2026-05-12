import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getRecommendations,
  getRecommenderStatus,
  ingestBook,
  submitFeedback,
  type IngestRequest,
  type RecommendationParams,
} from "../lib/api";

export function useRecommendations(params?: RecommendationParams) {
  return useQuery({
    queryKey: ["recommendations", params],
    queryFn: () => getRecommendations(params),
    enabled: Boolean(params?.book_ids?.length || params?.prompt),
  });
}

export function useRecommenderStatus() {
  return useQuery({
    queryKey: ["recommendations", "status"],
    queryFn: getRecommenderStatus,
  });
}

export function useIngestBook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: IngestRequest) => ingestBook(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

export function useSubmitFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ bookId, vote }: { bookId: string; vote: 1 | -1 }) =>
      submitFeedback(bookId, vote),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
