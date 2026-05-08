import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getGoals, setGoal } from "../lib/api";

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: getGoals,
  });
}

export function useSetGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ year, target }: { year: number; target: number }) =>
      setGoal(year, target),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}
