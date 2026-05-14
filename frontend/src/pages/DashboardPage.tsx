import { useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, CheckCircle2, ChevronLeft, ChevronRight, Clock, Flame } from "lucide-react";
import { Badge, Card, CardContent, CoverImage, Skeleton } from "@/components/ui";
import { useInProgress, useLibrary } from "@/hooks/useLibrary";
import { useStatistics } from "@/hooks/useStatistics";
import { formatDuration } from "@/lib/utils";
import type { LibraryBook } from "@/lib/api";

const PAGE_SIZE = 10;

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <Skeleton className="w-9 h-9 rounded-lg flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-8 w-14" />
          <Skeleton className="h-3 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div className="p-2 rounded-lg bg-accent/10 flex-shrink-0">
          <Icon className="w-5 h-5 text-accent" />
        </div>
        <div>
          <p className="text-3xl font-bold text-text-primary">{value}</p>
          <p className="text-sm text-text-secondary">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function BookCardSkeleton() {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-border last:border-0">
      <Skeleton className="w-10 h-14 rounded flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-1.5 w-full rounded-full" />
      </div>
      <Skeleton className="w-10 h-8 rounded flex-shrink-0" />
    </div>
  );
}

function InProgressCard({ book }: { book: LibraryBook }) {
  const pct = book.progress?.progress_pct ?? 0;
  const remaining = book.progress?.time_remaining;
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-border last:border-0">
      <CoverImage
        book={book}
        className="w-10 h-14 flex-shrink-0 bg-surface-hover rounded overflow-hidden flex items-center justify-center"
        iconClassName="w-4 h-4 text-text-secondary opacity-40"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text-primary truncate">{book.title}</p>
        <p className="text-xs text-text-secondary truncate">
          {book.authors.split(",").map((a, i, arr) => {
            const name = a.trim();
            return (
              <span key={name}>
                <Link to={`/authors/${encodeURIComponent(name)}`} className="hover:underline">
                  {name}
                </Link>
                {i < arr.length - 1 ? ", " : ""}
              </span>
            );
          })}
        </p>
        <div
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
          className="mt-1.5 h-1.5 bg-surface-hover rounded-full overflow-hidden"
        >
          <div className="h-full bg-accent rounded-full" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="flex-shrink-0 text-right min-w-[3rem]">
        <p className="text-sm font-medium text-text-primary">{Math.round(pct)}%</p>
        {remaining != null && (
          <p className="text-xs text-text-secondary">{formatDuration(remaining)}</p>
        )}
      </div>
    </div>
  );
}

function FinishedRow({ book }: { book: LibraryBook }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-border last:border-0">
      <CoverImage
        book={book}
        className="w-10 h-14 flex-shrink-0 bg-surface-hover rounded overflow-hidden flex items-center justify-center"
        iconClassName="w-4 h-4 text-text-secondary opacity-40"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text-primary truncate">{book.title}</p>
        <p className="text-xs text-text-secondary">
          {book.authors.split(",").map((a, i, arr) => {
            const name = a.trim();
            return (
              <span key={name}>
                <Link to={`/authors/${encodeURIComponent(name)}`} className="hover:underline">
                  {name}
                </Link>
                {i < arr.length - 1 ? ", " : ""}
              </span>
            );
          })}
        </p>
      </div>
      <Badge variant="positive">Done</Badge>
    </div>
  );
}

export default function DashboardPage() {
  const inProgress = useInProgress();
  const stats = useStatistics();
  const finished = useLibrary({ sort: "finished", limit: 5 });
  const [page, setPage] = useState(0);

  const currentYear = String(new Date().getFullYear());
  const thisYear = stats.data?.by_year.find((y) => y.year === currentYear)?.books ?? 0;
  const totalHours = stats.data ? Math.round(stats.data.hours_listened) : 0;
  const streak = stats.data?.streak.current ?? 0;

  const books = inProgress.data ?? [];
  const pageCount = Math.ceil(books.length / PAGE_SIZE);
  const pageBooks = books.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const recentlyFinished = (finished.data ?? []).filter((b) => b.progress?.is_finished).slice(0, 5);
  const statsLoading = stats.isLoading || inProgress.isLoading;

  return (
    <div className="space-y-8 p-6">
      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="In Progress" value={books.length} icon={BookOpen} />
            <StatCard label="Completed This Year" value={thisYear} icon={CheckCircle2} />
            <StatCard label="Total Hours" value={totalHours} icon={Clock} />
            <StatCard label="Day Streak" value={streak} icon={Flame} />
          </>
        )}
      </div>

      {/* Currently Listening */}
      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Currently Listening
          {books.length > 0 && (
            <span className="ml-2 text-sm font-normal text-text-secondary">({books.length})</span>
          )}
        </h2>
        <Card>
          <CardContent>
            {inProgress.isLoading ? (
              Array.from({ length: 5 }).map((_, i) => <BookCardSkeleton key={i} />)
            ) : books.length === 0 ? (
              <div className="text-center py-12 text-text-secondary">
                <BookOpen className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>No books in progress</p>
              </div>
            ) : (
              <>
                {pageBooks.map((book) => (
                  <InProgressCard key={book.id} book={book} />
                ))}
                {pageCount > 1 && (
                  <div className="flex items-center justify-between pt-3">
                    <p className="text-xs text-text-secondary">
                      {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, books.length)} of{" "}
                      {books.length}
                    </p>
                    <div className="flex gap-1">
                      <button
                        onClick={() => setPage((p) => p - 1)}
                        disabled={page === 0}
                        className="p-1 rounded text-text-secondary hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed"
                        aria-label="Previous page"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setPage((p) => p + 1)}
                        disabled={page >= pageCount - 1}
                        className="p-1 rounded text-text-secondary hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed"
                        aria-label="Next page"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Recently Finished */}
      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-4">Recently Finished</h2>
        <Card>
          <CardContent>
            {finished.isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 py-2.5 border-b border-border last:border-0"
                >
                  <Skeleton className="w-10 h-14 rounded flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))
            ) : recentlyFinished.length === 0 ? (
              <p className="text-sm text-text-secondary text-center py-6">No finished books yet</p>
            ) : (
              recentlyFinished.map((book) => <FinishedRow key={book.id} book={book} />)
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
