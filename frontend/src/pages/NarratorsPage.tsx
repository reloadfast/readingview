import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ChevronDown, ChevronUp, Mic, Search } from "lucide-react";
import { Badge, Input, Skeleton } from "@/components/ui";
import { useNarratorDetail, useNarrators } from "@/hooks/useNarrators";
import type { NarratorSummary } from "@/lib/api";

// ---------------------------------------------------------------------------
// Skeletons
// ---------------------------------------------------------------------------

function NarratorCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
      <Skeleton className="h-4 w-32" />
      <div className="flex gap-4">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
      </div>
      <Skeleton className="h-3 w-48" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expanded detail (lazy-loaded)
// ---------------------------------------------------------------------------

function NarratorDetailPanel({ name }: { name: string }) {
  const { data, isLoading } = useNarratorDetail(name);

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
            <p className="text-sm text-text-primary truncate">{book.title}</p>
            <Link
          to={`/authors/${encodeURIComponent(book.author)}`}
          className="text-xs text-text-secondary hover:text-accent hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {book.author}
        </Link>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-text-secondary">{book.duration_formatted}</span>
            {book.is_finished && <Badge variant="positive">Done</Badge>}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Narrator card
// ---------------------------------------------------------------------------

function NarratorCard({ narrator }: { narrator: NarratorSummary }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="p-4 rounded-xl bg-surface border border-border">
      <button
        className="w-full flex items-start justify-between gap-2 text-left"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-text-primary">{narrator.name}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1">
            <span className="text-xs text-text-secondary">
              {narrator.book_count} book{narrator.book_count !== 1 ? "s" : ""}
            </span>
            <span className="text-xs text-text-secondary">
              {narrator.total_hours.toFixed(1)}h
            </span>
            {narrator.finished_count > 0 && (
              <span className="text-xs text-text-secondary">
                {narrator.finished_count} finished
              </span>
            )}
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-text-secondary flex-shrink-0 mt-0.5" />
        ) : (
          <ChevronDown className="w-4 h-4 text-text-secondary flex-shrink-0 mt-0.5" />
        )}
      </button>

      {expanded && <NarratorDetailPanel name={narrator.name} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState({ filtered }: { filtered: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
      <Mic className="w-12 h-12 text-text-secondary opacity-30" />
      <p className="text-lg font-medium text-text-primary">
        {filtered ? "No narrators match your search" : "No narrators found"}
      </p>
      {!filtered && (
        <p className="text-sm text-text-secondary">
          Narrators from your library will appear here.
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function NarratorsPage() {
  const [search, setSearch] = useState("");
  const [searchParams] = useSearchParams();
  const sortByBooks = searchParams.get("sort") === "books";
  const { data, isLoading } = useNarrators();

  const sorted = [...(data ?? [])].sort((a, b) =>
    sortByBooks
      ? b.book_count - a.book_count
      : a.name.toLowerCase().localeCompare(b.name.toLowerCase())
  );
  const filtered = sorted.filter((n) =>
    search ? n.name.toLowerCase().includes(search.toLowerCase()) : true
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-text-primary">Narrators</h1>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
          <Input
            className="pl-8 w-52"
            placeholder="Filter narrators…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <NarratorCardSkeleton key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState filtered={Boolean(search)} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((narrator) => (
            <NarratorCard key={narrator.name} narrator={narrator} />
          ))}
        </div>
      )}
    </div>
  );
}
