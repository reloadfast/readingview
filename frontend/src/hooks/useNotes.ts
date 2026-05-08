import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteNote, getNote, upsertNote } from "../lib/api";

export function useNote(absItemId: string) {
  return useQuery({
    queryKey: ["note", absItemId],
    queryFn: () => getNote(absItemId),
  });
}

export function useSaveNote(absItemId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => upsertNote(absItemId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["note", absItemId] }),
  });
}

export function useDeleteNote(absItemId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteNote(absItemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["note", absItemId] }),
  });
}
