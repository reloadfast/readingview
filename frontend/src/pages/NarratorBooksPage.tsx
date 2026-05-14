import { useParams, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, BookOpen } from "lucide-react";
import { Badge, Card, CardContent, Skeleton } from "@/components/ui";
import { useNarratorDetail } from "@/hooks/useNarrators";

function BookRowSkeleton() {
  return (
    <div className="py-3 flex items-start justify-between gap-3 border-b border-border last:border-0">
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-32" />
      </div>
      <Skeleton className="h-3 w-16 flex-shrink-0" />
    </div>
  );
}

export default function NarratorBooksPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useNarratorDetail(name ?? "");

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-1.5 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{name}</h1>
          {data && (
            <p className="text-sm text-text-secondary mt-0.5">
              {data.book_count} book{data.book_count !== 1 ? "s" : ""} ·{" "}
              {data.total_hours.toFixed(1)}h · {data.finished_count} finished
            </p>
          )}
        </div>
      </div>

      <Card>
        <CardContent>
          {isLoading ? (
            <div>
              {Array.from({ length: 5 }).map((_, i) => (
                <BookRowSkeleton key={i} />
              ))}
            </div>
          ) : !data || data.books.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
              <BookOpen className="w-12 h-12 text-text-secondary opacity-30" />
              <p className="text-sm text-text-secondary">No books found for this narrator.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {data.books.map((book) => (
                <div key={book.id} className="py-3 flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">{book.title}</p>
                    {book.author && (
                      <Link
                        to={`/authors/${encodeURIComponent(book.author)}`}
                        className="text-xs text-text-secondary hover:text-accent hover:underline"
                      >
                        {book.author}
                      </Link>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {book.duration > 0 && (
                      <span className="text-xs text-text-secondary">{book.duration_formatted}</span>
                    )}
                    {book.is_finished && <Badge variant="positive">Done</Badge>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
