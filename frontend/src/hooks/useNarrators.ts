import { useQuery } from "@tanstack/react-query";
import { getNarratorDetail, getNarrators } from "../lib/api";

export function useNarrators() {
  return useQuery({
    queryKey: ["narrators"],
    queryFn: getNarrators,
  });
}

export function useNarratorDetail(name: string) {
  return useQuery({
    queryKey: ["narrators", name],
    queryFn: () => getNarratorDetail(name),
    enabled: Boolean(name),
  });
}
