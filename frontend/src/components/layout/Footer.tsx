import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";

export function Footer() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: Infinity,
  });

  return (
    <footer className="flex h-9 shrink-0 items-center border-t border-border bg-background px-6">
      <span className="text-xs text-text-secondary">
        {data?.version ? `v${data.version}` : "ReadingView"}
      </span>
    </footer>
  );
}
