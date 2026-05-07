import { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp } from "lucide-react";
import { Badge, Select, Skeleton } from "@/components/ui";
import { useSeries, useSeriesDetail } from "@/hooks/useSeries";
import type { SeriesSummary } from "@/lib/api";

// ---------------------------------------------------------------------------
// Progress bar
// ---------------------------------------------------------------------------

function ProgressBar({ percent }: { percent: number }) {
  const fill =
    percent === 100
      ? "bg-accent-positive"
      : percent > 0
        ? "bg-accent-warning"
        : "bg-border";

  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-1.5 w-full rounded-full bg-surface-hover overflow-hidden"
    >
      <div className={`h-full rounded-full transition-all ${fill}`} style={{ width: `${percent}%` }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeletons
// ---------------------------------------------------------------------------

function SeriesCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-1.5 w-full rounded-full" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Book status badge
// ---------------------------------------------------------------------------

function BookStatusBadge({ finished, progress }: { finished: boolean; progress: number }) {
  if (finished) return <Badge variant="positive">Finished</Badge>;
  if (progress > 0) return <Badge variant="warning">In Progress</Badge>;
  return <Badge variant="neutral">Not Started</Badge>;
}

// ---------------------------------------------------------------------------
// Series detail panel (lazy-loaded on expand)
// ---------------------------------------------------------------------------

function SeriesDetailPanel({ name }: { name: string }) {
  const { data, isLoading } = useSeriesDetail(name);

  if (isLoading) {
    return (
      <div className="mt-3 space-y-1.5 pt-3 border-t border-border">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mt-3 pt-3 border-t border-border divide-y divide-border">
      {data.books.map((book) => (
        <div key={book.id} className="py-2 flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text-primary truncate">
              {book.sequence ? `${book.sequence}. ` : ""}
              {book.title}
            </p>
            <p className="text-xs text-text-secondary">{book.duration_formatted}</p>
          </div>
          <BookStatusBadge finished={book.is_finished} progress={book.progress} />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Series card
// ---------------------------------------------------------------------------

function SeriesCard({ series }: { series: SeriesSummary }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="p-4 rounded-xl bg-surface border border-border">
      <button
        className="w-full flex items-start justify-between gap-2 text-left"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <div className="flex-1 min-w-0 space-y-2">
          <p className="text-sm font-semibold text-text-primary truncate">{series.name}</p>
          <p className="text-xs text-text-secondary">{series.author}</p>
          <ProgressBar percent={series.percent_complete} />
          <p className="text-xs text-text-secondary">
            {series.finished}/{series.total} book{series.total !== 1 ? "s" : ""} completed
          </p>
        </div>
        <div className="flex-shrink-0 mt-0.5">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-text-secondary" />
          ) : (
            <ChevronDown className="w-4 h-4 text-text-secondary" />
          )}
        </div>
      </button>

      {expanded && <SeriesDetailPanel name={series.name} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sort
// ---------------------------------------------------------------------------

type SortKey = "completion" | "title" | "count";

const SORT_OPTIONS = [
  { value: "completion", label: "Completion %" },
  { value: "title",      label: "Title A–Z" },
  { value: "count",      label: "Book Count" },
];

function sortSeries(data: SeriesSummary[], key: SortKey): SeriesSummary[] {
  return [...data].sort((a, b) => {
    if (key === "completion") return b.percent_complete - a.percent_complete;
    if (key === "title")      return a.name.localeCompare(b.name);
    return b.total - a.total;
  });
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SeriesPage() {
  const [sort, setSort] = useState<SortKey>("completion");
  const { data, isLoading } = useSeries();

  const sorted = sortSeries(data ?? [], sort);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-text-primary">Series</h1>
        <Select
          options={SORT_OPTIONS}
          value={sort}
          onValueChange={(v) => setSort(v as SortKey)}
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SeriesCardSkeleton key={i} />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
          <BookOpen className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-lg font-medium text-text-primary">No series found</p>
          <p className="text-sm text-text-secondary">
            Books with series metadata in your library will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sorted.map((series) => (
            <SeriesCard key={series.name} series={series} />
          ))}
        </div>
      )}
    </div>
  );
}
