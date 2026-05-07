import { Menu } from "lucide-react";
import { useLocation } from "react-router-dom";
import { Button } from "@/components/ui/Button";

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

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? "ReadingView";

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
    </header>
  );
}
