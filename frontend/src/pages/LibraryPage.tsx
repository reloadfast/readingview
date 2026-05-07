import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import * as Tabs from "@radix-ui/react-tabs";
import { BookOpen, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Badge, Input, Select, Skeleton } from "@/components/ui";
import { useInProgress, useLibrary } from "@/hooks/useLibrary";
import { formatDuration } from "@/lib/utils";
import type { LibraryBook, LibraryParams } from "@/lib/api";

const PAGE_LIMIT = 20;

const SORT_OPTIONS: { value: NonNullable<LibraryParams["sort"]>; label: string }[] = [
  { value: "title", label: "Title A–Z" },
  { value: "updated", label: "Recently Updated" },
  { value: "progress_asc", label: "Progress" },
  { value: "finished", label: "Recently Finished" },
];

function CoverImage({ book }: { book: LibraryBook }) {
  const [errored, setErrored] = useState(false);
  const src = !errored && book.cover_url ? book.cover_url : null;
  return (
    <div className="aspect-[2/3] bg-surface-hover rounded-lg overflow-hidden flex items-center justify-center">
      {src ? (
        <img
          src={src}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
        />
      ) : (
        <BookOpen className="w-8 h-8 text-text-secondary opacity-40" />
      )}
    </div>
  );
}

function BookCard({ book }: { book: LibraryBook }) {
  const pct = book.progress?.progress_pct ?? 0;
  const remaining = book.progress?.time_remaining;
  const isFinished = book.progress?.is_finished ?? false;

  return (
    <div className="flex flex-col gap-2">
      <CoverImage book={book} />
      <p className="text-sm font-medium text-text-primary line-clamp-2">{book.title}</p>
      <p className="text-xs text-text-secondary line-clamp-1">{book.authors}</p>
      {book.narrator && (
        <p className="text-xs text-text-secondary line-clamp-1">Narrated by {book.narrator}</p>
      )}
      {book.progress && (
        <>
          <div
            role="progressbar"
            aria-valuenow={Math.round(pct)}
            aria-valuemin={0}
            aria-valuemax={100}
            className="h-1.5 bg-surface-hover rounded-full overflow-hidden"
          >
            <div className="h-full bg-accent rounded-full" style={{ width: `${pct}%` }} />
          </div>
          {isFinished ? (
            <Badge variant="positive" className="self-start">
              Done
            </Badge>
          ) : remaining != null ? (
            <span className="text-xs text-text-secondary">{formatDuration(remaining)} remaining</span>
          ) : null}
        </>
      )}
    </div>
  );
}

function BookCardSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      <Skeleton className="aspect-[2/3] w-full rounded-lg" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-2/5" />
      <Skeleton className="h-1.5 w-full rounded-full" />
    </div>
  );
}

function BookGrid({ books, isLoading }: { books: LibraryBook[] | undefined; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <BookCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  if (!books || books.length === 0) {
    return (
      <div className="text-center py-16 text-text-secondary">
        <BookOpen className="w-10 h-10 mx-auto mb-2 opacity-40" />
        <p>No books found</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {books.map((book) => (
        <BookCard key={book.id} book={book} />
      ))}
    </div>
  );
}

export default function LibraryPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const tab = searchParams.get("tab") ?? "all";
  const page = parseInt(searchParams.get("page") ?? "1", 10);
  const sort = (searchParams.get("sort") ?? "title") as NonNullable<LibraryParams["sort"]>;
  const urlSearch = searchParams.get("search") ?? "";

  const [searchInput, setSearchInput] = useState(urlSearch);

  // Debounce search → URL
  useEffect(() => {
    const t = setTimeout(() => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (searchInput) next.set("search", searchInput);
          else next.delete("search");
          next.set("page", "1");
          return next;
        },
        { replace: true },
      );
    }, 300);
    return () => clearTimeout(t);
  }, [searchInput]); // eslint-disable-line react-hooks/exhaustive-deps

  const allBooks = useLibrary({
    ...(urlSearch ? { search: urlSearch } : {}),
    sort,
    page,
    limit: PAGE_LIMIT,
  });
  const inProgress = useInProgress();

  const filteredInProgress = (inProgress.data ?? []).filter((book) => {
    if (!urlSearch) return true;
    const q = urlSearch.toLowerCase();
    return (
      book.title.toLowerCase().includes(q) ||
      book.authors.toLowerCase().includes(q) ||
      (book.narrator ?? "").toLowerCase().includes(q)
    );
  });

  function setTab(t: string) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("tab", t);
        next.delete("page");
        return next;
      },
      { replace: true },
    );
  }

  function setSort(s: string) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("sort", s);
        next.set("page", "1");
        return next;
      },
      { replace: true },
    );
  }

  function setPage(p: number) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("page", String(p));
        return next;
      },
      { replace: true },
    );
  }

  const hasNextPage = tab === "all" && (allBooks.data?.length ?? 0) === PAGE_LIMIT;

  return (
    <div className="p-6 space-y-6">
      <Tabs.Root value={tab} onValueChange={setTab}>
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Tabs.List className="flex gap-1 bg-surface rounded-lg p-1">
            <Tabs.Trigger
              value="all"
              className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
            >
              All Books
            </Tabs.Trigger>
            <Tabs.Trigger
              value="inprogress"
              className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
            >
              In Progress
            </Tabs.Trigger>
          </Tabs.List>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
              <Input
                className="pl-8 w-52"
                placeholder="Search title, author, narrator…"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            {tab === "all" && (
              <Select
                options={SORT_OPTIONS}
                value={sort}
                onValueChange={setSort}
              />
            )}
          </div>
        </div>

        {/* All Books tab */}
        <Tabs.Content value="all" className="mt-6 space-y-6">
          <BookGrid books={allBooks.data} isLoading={allBooks.isLoading} />
          {!allBooks.isLoading && (allBooks.data?.length ?? 0) > 0 && (
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-border text-text-secondary hover:bg-surface-hover disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" /> Prev
              </button>
              <span className="text-sm text-text-secondary">Page {page}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={!hasNextPage}
                className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-border text-text-secondary hover:bg-surface-hover disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </Tabs.Content>

        {/* In Progress tab */}
        <Tabs.Content value="inprogress" className="mt-6">
          <BookGrid books={filteredInProgress} isLoading={inProgress.isLoading} />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
