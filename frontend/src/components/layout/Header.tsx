import { Menu, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/Button";
import { refreshAbsCache } from "@/lib/api";

const PAGE_TITLES: Record<string, string> = {
  "/":            "Dashboard",
  "/library":     "Library",
  "/statistics":  "Statistics",
  "/authors":     "Authors",
  "/narrators":   "Narrators",
  "/series":      "Series",
  "/releases":    "Releases",
  "/collections": "Collections",
  "/settings":    "Settings",
};

const ABS_QUERY_KEYS = ["library", "statistics", "series", "narrators", "authors"];

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? "ReadingView";
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshAbsCache();
      for (const key of ABS_QUERY_KEYS) {
        void queryClient.invalidateQueries({ queryKey: [key] });
      }
    } catch {
      // silently ignore — user can retry
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background px-6">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenuClick}
        aria-label="Open menu"
      >
        <Menu className="h-4 w-4" />
      </Button>
      <h1 className="text-base font-semibold text-text-primary">{title}</h1>
      <div className="ml-auto">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleRefresh}
          disabled={refreshing}
          aria-label="Refresh data from Audiobookshelf"
          title="Refresh data from Audiobookshelf"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
        </Button>
      </div>
    </header>
  );
}
