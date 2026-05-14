import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import * as Tabs from "@radix-ui/react-tabs";
import { Search, User, UserMinus, UserPlus } from "lucide-react";
import { Badge, Input, Skeleton } from "@/components/ui";
import {
  useAuthors,
  useFollowAuthor,
  useLibraryAuthors,
  useSearchAuthors,
  useUnfollowAuthor,
} from "@/hooks/useAuthors";
import type { LibraryAuthor, TrackedAuthorOut } from "@/lib/api";

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

function AuthorPhoto({ url, name }: { url: string | null; name: string }) {
  const [errored, setErrored] = useState(false);
  if (url && !errored) {
    return (
      <img
        src={url}
        alt={name}
        className="rounded-full w-16 h-16 object-cover flex-shrink-0"
        onError={() => setErrored(true)}
      />
    );
  }
  return (
    <div className="rounded-full w-16 h-16 bg-surface-hover flex items-center justify-center flex-shrink-0">
      <User className="w-7 h-7 text-text-secondary opacity-40" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Followed Authors tab
// ---------------------------------------------------------------------------

function AuthorCardSkeleton() {
  return (
    <div className="flex items-start gap-4 p-4 rounded-xl bg-surface border border-border">
      <Skeleton className="rounded-full w-16 h-16 flex-shrink-0" />
      <div className="flex-1 space-y-2 pt-1">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-48" />
        <Skeleton className="h-3 w-36" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
    </div>
  );
}

function AuthorCard({
  author,
  bookCount,
}: {
  author: TrackedAuthorOut;
  bookCount: number;
}) {
  const [confirming, setConfirming] = useState(false);
  const unfollow = useUnfollowAuthor();
  const canUnfollow = Boolean(author.ol_key);

  return (
    <div className="flex items-start gap-4 p-4 rounded-xl bg-surface border border-border">
      <AuthorPhoto url={author.photo_url ?? null} name={author.name} />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-semibold text-text-primary">{author.name}</p>
          {bookCount > 0 && (
            <Badge variant="neutral" className="flex-shrink-0">
              {bookCount} book{bookCount !== 1 ? "s" : ""}
            </Badge>
          )}
        </div>
        {author.bio && (
          <p className="text-xs text-text-secondary mt-1 line-clamp-2">{author.bio}</p>
        )}
        <div className="mt-2">
          {confirming ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary">Unfollow?</span>
              <button
                className="text-xs text-red-500 hover:underline"
                onClick={() => {
                  if (author.ol_key) unfollow.mutate(author.ol_key);
                  setConfirming(false);
                }}
              >
                Yes
              </button>
              <button
                className="text-xs text-text-secondary hover:underline"
                onClick={() => setConfirming(false)}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              disabled={!canUnfollow || unfollow.isPending}
              onClick={() => setConfirming(true)}
              className="flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <UserMinus className="w-3.5 h-3.5" />
              Unfollow
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function FollowSearch({ followedKeys }: { followedKeys: Set<string> }) {
  const [q, setQ] = useState("");
  const search = useSearchAuthors(q);
  const follow = useFollowAuthor();

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
        <Input
          className="pl-8 w-72"
          placeholder="Search Open Library for an author…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {q.length > 0 && (
        <div className="border border-border rounded-xl divide-y divide-border overflow-hidden max-h-72 overflow-y-auto">
          {search.isLoading && (
            <div className="px-4 py-3 text-sm text-text-secondary">Searching…</div>
          )}
          {!search.isLoading && (search.data?.length ?? 0) === 0 && (
            <div className="px-4 py-3 text-sm text-text-secondary">No results</div>
          )}
          {search.data?.map((result) => {
            const already = followedKeys.has(result.ol_key);
            return (
              <div key={result.ol_key} className="flex items-center gap-3 px-4 py-3 bg-surface">
                <AuthorPhoto url={result.photo_url ?? null} name={result.name} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{result.name}</p>
                  {result.top_work && (
                    <p className="text-xs text-text-secondary line-clamp-1">{result.top_work}</p>
                  )}
                  <p className="text-xs text-text-secondary">{result.work_count} works</p>
                </div>
                <button
                  disabled={already || follow.isPending}
                  onClick={() => {
                    follow.mutate({ name: result.name, ol_key: result.ol_key });
                    setQ("");
                  }}
                  className="flex items-center gap-1 text-sm text-accent hover:text-accent/80 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
                >
                  <UserPlus className="w-4 h-4" />
                  {already ? "Following" : "Follow"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FollowedTab({
  authors,
  isLoading,
  bookCountMap,
  followedKeys,
}: {
  authors: TrackedAuthorOut[];
  isLoading: boolean;
  bookCountMap: Map<string, number>;
  followedKeys: Set<string>;
}) {
  return (
    <div className="space-y-6">
      <FollowSearch followedKeys={followedKeys} />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <AuthorCardSkeleton key={i} />
          ))}
        </div>
      ) : authors.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <User className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-lg font-medium text-text-primary">Not following anyone yet</p>
          <p className="text-sm text-text-secondary">
            Use the search above to find and follow authors.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {authors.map((author) => (
            <AuthorCard
              key={author.id}
              author={author}
              bookCount={bookCountMap.get(author.name) ?? 0}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Library Authors tab
// ---------------------------------------------------------------------------

function LibraryAuthorsTab({
  authors,
  isLoading,
  followedNames,
  sortByBooks,
}: {
  authors: LibraryAuthor[];
  isLoading: boolean;
  followedNames: Set<string>;
  sortByBooks?: boolean;
}) {
  const follow = useFollowAuthor();

  const sorted = sortByBooks
    ? [...authors].sort((a, b) => b.book_count - a.book_count)
    : authors;

  if (isLoading) {
    return (
      <div className="space-y-1">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-11 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
        <User className="w-12 h-12 text-text-secondary opacity-30" />
        <p className="text-sm text-text-secondary">No authors found in your library</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {sorted.map((a) => {
        const already = followedNames.has(a.name);
        return (
          <div
            key={a.name}
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-surface-hover"
          >
            <span className="text-sm text-text-primary flex-1">{a.name}</span>
            <Badge variant="neutral" className="flex-shrink-0">
              {a.book_count} book{a.book_count !== 1 ? "s" : ""}
            </Badge>
            <button
              disabled={already || follow.isPending}
              onClick={() => follow.mutate({ name: a.name })}
              className="flex items-center gap-1 text-xs text-accent hover:text-accent/80 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            >
              <UserPlus className="w-3.5 h-3.5" />
              {already ? "Following" : "Follow"}
            </button>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AuthorsPage() {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") === "library" ? "library" : "followed";
  const sortByBooks = searchParams.get("sort") === "books";
  const [activeTab, setActiveTab] = useState(initialTab);

  const followed = useAuthors();
  const library = useLibraryAuthors();

  const bookCountMap = new Map(
    (library.data ?? []).map((a) => [a.name, a.book_count])
  );
  const followedKeys = new Set(
    (followed.data ?? [])
      .map((a) => a.ol_key)
      .filter((k): k is string => k !== null)
  );
  const followedNames = new Set((followed.data ?? []).map((a) => a.name));

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-text-primary">Authors</h1>

      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List className="flex gap-1 bg-surface rounded-lg p-1 w-fit">
          <Tabs.Trigger
            value="followed"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            Following
          </Tabs.Trigger>
          <Tabs.Trigger
            value="library"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            In Your Library
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="followed" className="mt-6">
          <FollowedTab
            authors={followed.data ?? []}
            isLoading={followed.isLoading}
            bookCountMap={bookCountMap}
            followedKeys={followedKeys}
          />
        </Tabs.Content>

        <Tabs.Content value="library" className="mt-6">
          <LibraryAuthorsTab
            authors={library.data ?? []}
            isLoading={library.isLoading}
            followedNames={followedNames}
            sortByBooks={sortByBooks}
          />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
