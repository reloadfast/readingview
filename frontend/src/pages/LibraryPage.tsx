import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  NotebookPen,
  Search,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { Badge, CoverImage, Input, Select, Skeleton } from "@/components/ui";
import { useInProgress, useLibrary } from "@/hooks/useLibrary";
import { useDeleteNote, useNote, useSaveNote } from "@/hooks/useNotes";
import { useRecommendations, useSubmitFeedback } from "@/hooks/useRecommendations";
import { formatDuration } from "@/lib/utils";
import type { LibraryBook, LibraryParams, Recommendation } from "@/lib/api";

const PAGE_LIMIT = 20;

const SORT_OPTIONS: { value: NonNullable<LibraryParams["sort"]>; label: string }[] = [
  { value: "title", label: "Title A–Z" },
  { value: "updated", label: "Recently Updated" },
  { value: "progress_asc", label: "Progress" },
  { value: "finished", label: "Recently Finished" },
];

function SimilarRecCard({ rec }: { rec: Recommendation }) {
  const [localFeedback, setLocalFeedback] = useState(rec.feedback);
  const { mutate, isPending } = useSubmitFeedback();
  const authors = Array.isArray(rec.authors) ? rec.authors.join(", ") : rec.authors;

  function vote(v: 1 | -1) {
    setLocalFeedback(v);
    mutate({ bookId: rec.book_id, vote: v });
  }

  return (
    <div className="flex gap-3 p-3 rounded-xl border border-border bg-surface-hover">
      <div className="aspect-[2/3] w-12 shrink-0 rounded bg-surface flex items-center justify-center overflow-hidden">
        {rec.cover_id ? (
          <img
            src={`https://covers.openlibrary.org/b/id/${rec.cover_id}-M.jpg`}
            alt={rec.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <BookOpen className="w-4 h-4 text-text-secondary opacity-40" />
        )}
      </div>
      <div className="flex flex-col gap-1 flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary line-clamp-2">{rec.title}</p>
        <p className="text-xs text-text-secondary line-clamp-1">{authors}</p>
        <div className="flex gap-1 mt-auto pt-1">
          <button
            onClick={() => vote(1)}
            disabled={isPending}
            title="Good recommendation"
            className={`p-1 rounded transition-colors disabled:opacity-40 ${
              localFeedback > 0
                ? "text-accent bg-accent/10"
                : "text-text-secondary hover:text-text-primary hover:bg-surface"
            }`}
          >
            <ThumbsUp className="w-3 h-3" />
          </button>
          <button
            onClick={() => vote(-1)}
            disabled={isPending}
            title="Not interested"
            className={`p-1 rounded transition-colors disabled:opacity-40 ${
              localFeedback < 0
                ? "text-red-500 bg-red-500/10"
                : "text-text-secondary hover:text-text-primary hover:bg-surface"
            }`}
          >
            <ThumbsDown className="w-3 h-3" />
          </button>
          <span className="text-xs text-text-secondary opacity-60 ml-auto self-center">
            {Math.round(rec.score * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
}

function SimilarSlideOver({ book }: { book: LibraryBook }) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useRecommendations(
    open ? { book_ids: [book.id] } : undefined,
  );

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          title="Find similar books"
          className="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Similar
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content
          className="fixed right-0 inset-y-0 z-50 w-full max-w-sm bg-surface border-l border-border shadow-xl focus:outline-none flex flex-col"
          style={{ transition: "transform 200ms" }}
        >
          <div className="flex items-start justify-between p-4 border-b border-border shrink-0">
            <div>
              <Dialog.Title className="text-sm font-semibold text-text-primary">
                Similar to
              </Dialog.Title>
              <p className="text-xs text-text-secondary line-clamp-1 mt-0.5">{book.title}</p>
            </div>
            <Dialog.Close asChild>
              <button className="text-text-secondary hover:text-text-primary ml-4 shrink-0">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {isLoading && (
              <>
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-xl border border-border">
                    <Skeleton className="w-12 aspect-[2/3] rounded shrink-0" />
                    <div className="flex flex-col gap-2 flex-1">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </>
            )}
            {!isLoading && (!data || data.length === 0) && (
              <div className="text-center py-12 text-text-secondary">
                <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No similar books found.</p>
                <p className="text-xs mt-1 opacity-70">Try ingesting more books via the Recommendations page.</p>
              </div>
            )}
            {data?.map((rec) => (
              <SimilarRecCard key={rec.book_id} rec={rec} />
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function NotesDialog({ book }: { book: LibraryBook }) {
  const [open, setOpen] = useState(false);
  const { data } = useNote(book.id);
  const save = useSaveNote(book.id);
  const del = useDeleteNote(book.id);
  const [draft, setDraft] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleOpen(isOpen: boolean) {
    if (isOpen) setDraft(data?.body ?? "");
    setOpen(isOpen);
  }

  function handleSave() {
    if (draft.trim()) {
      save.mutate(draft.trim(), { onSuccess: () => setOpen(false) });
    } else {
      del.mutate(undefined, { onSuccess: () => setOpen(false) });
    }
  }

  const hasNote = Boolean(data?.body);

  return (
    <Dialog.Root open={open} onOpenChange={handleOpen}>
      <Dialog.Trigger asChild>
        <button
          title="Notes"
          className={`flex items-center gap-1 text-xs px-1.5 py-0.5 rounded hover:bg-surface-hover transition-colors ${hasNote ? "text-accent" : "text-text-secondary"}`}
        >
          <NotebookPen className="w-3.5 h-3.5" />
          {hasNote ? "Note" : "Add note"}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-surface border border-border rounded-xl p-5 shadow-xl focus:outline-none"
          onOpenAutoFocus={(e) => {
            e.preventDefault();
            textareaRef.current?.focus();
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <Dialog.Title className="text-sm font-semibold text-text-primary line-clamp-2 pr-4">
              {book.title}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="text-text-secondary hover:text-text-primary shrink-0">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>
          <textarea
            ref={textareaRef}
            className="w-full h-36 resize-none rounded-lg border border-border bg-surface-hover px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Your personal notes…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="flex justify-end gap-2 mt-3">
            {hasNote && (
              <button
                onClick={() => del.mutate(undefined, { onSuccess: () => setOpen(false) })}
                disabled={del.isPending}
                className="px-3 py-1.5 text-sm rounded-lg border border-border text-text-secondary hover:bg-surface-hover disabled:opacity-40"
              >
                Clear
              </button>
            )}
            <button
              onClick={handleSave}
              disabled={save.isPending || del.isPending}
              className="px-3 py-1.5 text-sm rounded-lg bg-accent text-white hover:opacity-90 disabled:opacity-40"
            >
              Save
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
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
      <p className="text-xs text-text-secondary line-clamp-1">
        {book.authors.split(",").map((a, i, arr) => {
          const name = a.trim();
          return (
            <span key={name}>
              <Link
                to={`/authors/${encodeURIComponent(name)}`}
                className="hover:text-accent hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                {name}
              </Link>
              {i < arr.length - 1 ? ", " : ""}
            </span>
          );
        })}
      </p>
      {book.narrator && (
        <p className="text-xs text-text-secondary line-clamp-1">
          Narrated by{" "}
          {book.narrator.split(",").map((n, i, arr) => {
            const name = n.trim();
            return (
              <span key={name}>
                <Link
                  to={`/narrators/${encodeURIComponent(name)}`}
                  className="hover:text-accent hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {name}
                </Link>
                {i < arr.length - 1 ? ", " : ""}
              </span>
            );
          })}
        </p>
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
      <div className="flex items-center gap-2">
        <NotesDialog book={book} />
        <SimilarSlideOver book={book} />
      </div>
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
