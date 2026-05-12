import { useQuery } from "@tanstack/react-query";
import { getBook, getInProgress, getLibrary, type LibraryParams } from "../lib/api";
import { useWebSocket } from "../contexts/WebSocketContext";

export function useLibrary(params?: LibraryParams) {
  return useQuery({
    queryKey: ["library", params],
    queryFn: () => getLibrary(params),
  });
}

export function useInProgress() {
  const { connected } = useWebSocket();
  return useQuery({
    queryKey: ["library", "in-progress"],
    queryFn: getInProgress,
    staleTime: connected ? Infinity : 30_000,
  });
}


export function useBook(id: string) {
  return useQuery({
    queryKey: ["library", id],
    queryFn: () => getBook(id),
    enabled: Boolean(id),
  });
}
