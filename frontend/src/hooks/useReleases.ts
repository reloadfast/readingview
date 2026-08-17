import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addTrackedAuthor,
  createManualRelease,
  getManualReleases,
  getReleases,
  getTrackedAuthors,
  patchRelease,
  refreshReleases,
  removeTrackedAuthor,
  updateManualRelease,
  uploadManualReleaseCover,
  type ManualReleaseInput,
  type PatchReleaseRequest,
  type TrackAuthorRequest,
} from "../lib/api";

export function useReleases(author?: string, includeHidden = false) {
  return useQuery({
    queryKey: ["releases", author ?? null, includeHidden],
    queryFn: () => getReleases(author, includeHidden),
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
      void qc.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}

export function useRemoveTrackedAuthor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => removeTrackedAuthor(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["releases"] });
      void qc.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}

export function usePatchRelease() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: PatchReleaseRequest & { id: number }) =>
      patchRelease(id, body),
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

export function useManualReleases(includeArchived = false) {
  return useQuery({
    queryKey: ["manual-releases", includeArchived],
    queryFn: () => getManualReleases(includeArchived),
  });
}

function useManualReleaseInvalidation() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: ["manual-releases"] });
  };
}

export function useCreateManualRelease() {
  const invalidate = useManualReleaseInvalidation();
  return useMutation({ mutationFn: createManualRelease, onSuccess: invalidate });
}

export function useUpdateManualRelease() {
  const invalidate = useManualReleaseInvalidation();
  return useMutation({
    mutationFn: ({ id, ...body }: ManualReleaseInput & { id: number }) =>
      updateManualRelease(id, body),
    onSuccess: invalidate,
  });
}

export function useUploadManualReleaseCover() {
  const invalidate = useManualReleaseInvalidation();
  return useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => uploadManualReleaseCover(id, file),
    onSuccess: invalidate,
  });
}
