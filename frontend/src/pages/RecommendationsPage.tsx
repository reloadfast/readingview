import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import {
  Sparkles,
  BookOpen,
  ThumbsUp,
  ThumbsDown,
  X,
  Search,
  Settings,
  Plus,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Input, Skeleton } from "@/components/ui";
import { useLibrary } from "@/hooks/useLibrary";
import {
  useRecommendations,
  useRecommenderStatus,
  useIngestBook,
  useSubmitFeedback,
} from "@/hooks/useRecommendations";
import type { LibraryBook, Recommendation, RecommendationParams } from "@/lib/api";

function OLCover({ coverId, title }: { coverId: number | null; title: string }) {
  const [errored, setErrored] = useState(false);
  const src =
    coverId && !errored
      ? `https://covers.openlibrary.org/b/id/${coverId}-M.jpg`
      : null;
  return (
    <div className="aspect-[2/3] bg-surface-hover rounded-lg overflow-hidden flex items-center justify-center shrink-0 w-20">
      {src ? (
        <img
          src={src}
          alt={title}
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
        />
      ) : (
        <BookOpen className="w-6 h-6 text-text-secondary opacity-40" />
      )}
    </div>
  );
}

function ThumbButtons({ rec }: { rec: Recommendation }) {
  const [localFeedback, setLocalFeedback] = useState(rec.feedback);
  const { mutate, isPending } = useSubmitFeedback();

  function vote(v: 1 | -1) {
    setLocalFeedback(v);
    mutate({ bookId: rec.book_id, vote: v });
  }

  return (
    <div className="flex gap-1 mt-auto pt-2">
      <button
        onClick={() => vote(1)}
        disabled={isPending}
        title="Good recommendation"
        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors disabled:opacity-40 ${
          localFeedback > 0
            ? "bg-accent/20 text-accent"
            : "text-text-secondary hover:text-text-primary hover:bg-surface-hover"
        }`}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => vote(-1)}
        disabled={isPending}
        title="Not interested"
        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors disabled:opacity-40 ${
          localFeedback < 0
            ? "bg-red-500/20 text-red-500"
            : "text-text-secondary hover:text-text-primary hover:bg-surface-hover"
        }`}
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const authors = Array.isArray(rec.authors) ? rec.authors.join(", ") : rec.authors;
  const subjects = Array.isArray(rec.subjects) ? rec.subjects.slice(0, 3) : [];

  return (
    <div className="flex gap-3 p-3 rounded-xl border border-border bg-surface hover:bg-surface-hover transition-colors">
      <OLCover coverId={rec.cover_id} title={rec.title} />
      <div className="flex flex-col gap-1 flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary line-clamp-2">{rec.title}</p>
        <p className="text-xs text-text-secondary line-clamp-1">{authors}</p>
        {subjects.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-0.5">
            {subjects.map((s) => (
              <span
                key={s}
                className="text-xs px-1.5 py-0.5 rounded bg-surface-hover text-text-secondary"
              >
                {s}
              </span>
            ))}
          </div>
        )}
        {rec.explanation && (
          <p className="text-xs text-text-secondary line-clamp-3 mt-1 italic">{rec.explanation}</p>
        )}
        <div className="flex items-center justify-between mt-auto pt-1">
          <span className="text-xs text-text-secondary opacity-60">
            {Math.round(rec.score * 100)}% match
          </span>
          <ThumbButtons rec={rec} />
        </div>
      </div>
    </div>
  );
}

function ResultsGrid({ params }: { params: RecommendationParams | null }) {
  const { data, isLoading, isError } = useRecommendations(params ?? undefined);

  if (!params) return null;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex gap-3 p-3 rounded-xl border border-border">
            <Skeleton className="w-20 aspect-[2/3] rounded-lg shrink-0" />
            <div className="flex flex-col gap-2 flex-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-1/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mt-6 text-center py-12 text-text-secondary">
        <p className="text-sm">Failed to load recommendations. Is the recommender running?</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="mt-6 text-center py-12 text-text-secondary">
        <Sparkles className="w-10 h-10 mx-auto mb-2 opacity-30" />
        <p className="text-sm">No recommendations found. Try adjusting your prompt or adding more books.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6">
      {data.map((rec) => (
        <RecommendationCard key={rec.book_id} rec={rec} />
      ))}
    </div>
  );
}

function BookCheckbox({
  book,
  selected,
  onToggle,
}: {
  book: LibraryBook;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <label className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-surface-hover cursor-pointer">
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="accent-accent"
      />
      <span className="text-sm text-text-primary line-clamp-1 flex-1">{book.title}</span>
      <span className="text-xs text-text-secondary shrink-0 line-clamp-1">{book.authors}</span>
    </label>
  );
}

function IngestDialog() {
  const [open, setOpen] = useState(false);
  const { mutate, isPending, isError, error } = useIngestBook();
  const [form, setForm] = useState({ isbn: "", title: "", author: "", work_key: "" });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = Object.fromEntries(
      Object.entries(form).filter(([, v]) => v.trim() !== ""),
    ) as { isbn?: string; title?: string; author?: string; work_key?: string };
    mutate(body, { onSuccess: () => { setOpen(false); setForm({ isbn: "", title: "", author: "", work_key: "" }); } });
  }

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-border text-text-secondary hover:bg-surface-hover transition-colors">
          <Plus className="w-4 h-4" />
          Ingest book
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-sm bg-surface border border-border rounded-xl p-5 shadow-xl focus:outline-none">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-sm font-semibold text-text-primary">
              Ingest a book
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="text-text-secondary hover:text-text-primary">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>
          <form onSubmit={handleSubmit} className="space-y-3">
            {(["isbn", "title", "author", "work_key"] as const).map((field) => (
              <div key={field}>
                <label className="text-xs text-text-secondary capitalize block mb-1">
                  {field.replace("_", " ")}
                </label>
                <Input
                  value={form[field]}
                  onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                  placeholder={
                    field === "work_key"
                      ? "/works/OL123W"
                      : field === "isbn"
                      ? "9780316129084"
                      : ""
                  }
                />
              </div>
            ))}
            {isError && (
              <p className="text-xs text-red-500">
                {(error as Error)?.message ?? "Ingestion failed"}
              </p>
            )}
            <button
              type="submit"
              disabled={
                isPending ||
                !Object.values(form).some((v) => v.trim() !== "")
              }
              className="w-full py-2 text-sm rounded-lg bg-accent text-white hover:opacity-90 disabled:opacity-40"
            >
              {isPending ? "Ingesting…" : "Ingest"}
            </button>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default function RecommendationsPage() {
  const { data: status, isLoading: statusLoading } = useRecommenderStatus();
  const [activeTab, setActiveTab] = useState<"books" | "prompt">("books");
  const [selectedBookIds, setSelectedBookIds] = useState<string[]>([]);
  const [prompt, setPrompt] = useState("");
  const [bookSearch, setBookSearch] = useState("");
  const [submittedParams, setSubmittedParams] = useState<RecommendationParams | null>(null);

  const allBooks = useLibrary({ sort: "finished", limit: 200 });
  const finishedBooks = (allBooks.data ?? []).filter(
    (b) => b.progress?.is_finished,
  );
  const filteredBooks = finishedBooks.filter((b) => {
    if (!bookSearch) return true;
    const q = bookSearch.toLowerCase();
    return b.title.toLowerCase().includes(q) || b.authors.toLowerCase().includes(q);
  });

  function toggleBook(id: string) {
    setSelectedBookIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  function handleSubmit() {
    if (activeTab === "books" && selectedBookIds.length > 0) {
      setSubmittedParams({ book_ids: selectedBookIds });
    } else if (activeTab === "prompt" && prompt.trim()) {
      setSubmittedParams({ prompt: prompt.trim() });
    }
  }

  if (statusLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full rounded-xl" />
      </div>
    );
  }

  if (!status?.enabled) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-5 h-5 text-text-secondary" />
          <h1 className="text-lg font-semibold text-text-primary">Recommendations</h1>
        </div>
        <div className="rounded-xl border border-border bg-surface p-6 text-center max-w-md mx-auto mt-12">
          <Sparkles className="w-10 h-10 mx-auto mb-3 text-text-secondary opacity-40" />
          <p className="text-sm font-medium text-text-primary mb-1">Recommender not enabled</p>
          <p className="text-xs text-text-secondary mb-4">
            Configure and enable the AI book recommender in Settings to get personalised suggestions.
          </p>
          <Link
            to="/settings"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-accent text-white hover:opacity-90 transition-opacity"
          >
            <Settings className="w-4 h-4" />
            Go to Settings
          </Link>
        </div>
      </div>
    );
  }

  const canSubmit =
    (activeTab === "books" && selectedBookIds.length > 0) ||
    (activeTab === "prompt" && prompt.trim().length > 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-text-secondary" />
          <h1 className="text-lg font-semibold text-text-primary">Recommendations</h1>
          <span className="text-xs text-text-secondary px-2 py-0.5 rounded-full border border-border">
            {status.vector_backend} · {status.model}
          </span>
        </div>
        <IngestDialog />
      </div>

      <Tabs.Root
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as "books" | "prompt")}
      >
        <Tabs.List className="flex gap-1 bg-surface rounded-lg p-1 w-fit">
          <Tabs.Trigger
            value="books"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            By books
          </Tabs.Trigger>
          <Tabs.Trigger
            value="prompt"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            By prompt
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="books" className="mt-4">
          <div className="flex flex-col gap-3">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
              <Input
                className="pl-8"
                placeholder="Search finished books…"
                value={bookSearch}
                onChange={(e) => setBookSearch(e.target.value)}
              />
            </div>
            <div className="border border-border rounded-xl overflow-y-auto max-h-64 p-1 bg-surface">
              {allBooks.isLoading ? (
                <div className="p-4 text-sm text-text-secondary">Loading books…</div>
              ) : filteredBooks.length === 0 ? (
                <div className="p-4 text-sm text-text-secondary">
                  {finishedBooks.length === 0
                    ? "No finished books in your library yet."
                    : "No matches."}
                </div>
              ) : (
                filteredBooks.map((book) => (
                  <BookCheckbox
                    key={book.id}
                    book={book}
                    selected={selectedBookIds.includes(book.id)}
                    onToggle={() => toggleBook(book.id)}
                  />
                ))
              )}
            </div>
            {selectedBookIds.length > 0 && (
              <p className="text-xs text-text-secondary">
                {selectedBookIds.length} book{selectedBookIds.length !== 1 ? "s" : ""} selected
              </p>
            )}
          </div>
        </Tabs.Content>

        <Tabs.Content value="prompt" className="mt-4">
          <textarea
            className="w-full max-w-lg h-28 resize-none rounded-xl border border-border bg-surface-hover px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Describe what you're in the mood for… e.g. 'epic fantasy with magic systems' or 'cozy mysteries set in small towns'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </Tabs.Content>
      </Tabs.Root>

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-accent text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        <Sparkles className="w-4 h-4" />
        Get recommendations
      </button>

      <ResultsGrid params={submittedParams} />
    </div>
  );
}
