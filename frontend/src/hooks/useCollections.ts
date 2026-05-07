import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addToCollection,
  createCollection,
  deleteCollection,
  getCollection,
  getCollections,
  removeFromCollection,
  updateCollection,
  type CreateCollectionRequest,
  type PatchCollectionRequest,
} from "../lib/api";

export function useCollections() {
  return useQuery({
    queryKey: ["collections"],
    queryFn: getCollections,
  });
}

export function useCollectionDetail(id: number | null) {
  return useQuery({
    queryKey: ["collections", id],
    queryFn: () => getCollection(id!),
    enabled: id !== null,
  });
}

export function useCreateCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateCollectionRequest) => createCollection(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useUpdateCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: PatchCollectionRequest }) =>
      updateCollection(id, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useDeleteCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteCollection(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useAddToCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, absItemId }: { id: number; absItemId: string }) =>
      addToCollection(id, absItemId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useRemoveFromCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, itemId }: { id: number; itemId: string }) =>
      removeFromCollection(id, itemId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}
