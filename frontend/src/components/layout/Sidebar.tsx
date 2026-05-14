import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  BookOpen,
  BarChart3,
  Users,
  Mic,
  BookMarked,
  Calendar,
  FolderOpen,
  Sparkles,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  icon: LucideIcon;
  label: string;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/",            icon: LayoutDashboard, label: "Dashboard",   end: true },
  { to: "/library",     icon: BookOpen,        label: "Library"               },
  { to: "/statistics",  icon: BarChart3,       label: "Statistics"            },
  { to: "/authors",     icon: Users,           label: "Authors"               },
  { to: "/narrators",   icon: Mic,             label: "Narrators"             },
  { to: "/series",      icon: BookMarked,      label: "Series"                },
  { to: "/releases",    icon: Calendar,        label: "Releases"              },
  { to: "/collections",    icon: FolderOpen, label: "Collections"    },
  { to: "/recommendations", icon: Sparkles,   label: "Recommendations" },
  { to: "/settings",       icon: Settings,   label: "Settings"       },
];

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: Infinity,
  });

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 flex w-56 flex-col border-r border-border bg-surface",
        "transition-transform duration-200",
        "md:static md:translate-x-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex h-14 shrink-0 items-center border-b border-border px-4">
        <span className="text-sm font-semibold tracking-wide text-text-primary">ReadingView</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end ?? false}
            onClick={onMobileClose}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-surface-hover text-text-primary font-medium"
                  : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="shrink-0 border-t border-border px-3 py-2 flex items-center justify-between">
        <span className="text-xs text-text-secondary pl-1">
          {data?.version ? `v${data.version}` : ""}
        </span>
        <ThemeToggle />
      </div>
    </aside>
  );
}
