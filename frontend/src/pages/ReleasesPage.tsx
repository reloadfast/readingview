import { useState } from "react";
import { BookMarked, Check, HelpCircle, Pencil, RefreshCw, Search, Trash2 } from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { Badge, Input, Select, Skeleton } from "@/components/ui";
import {
  useAddTrackedAuthor,
  usePatchRelease,
  useRefreshReleases,
  useReleases,
  useRemoveTrackedAuthor,
  useTrackedAuthors,
} from "@/hooks/useReleases";
import { useSearchAuthors } from "@/hooks/useAuthors";
import { cn } from "@/lib/utils";
import type { ReleaseOut, ReleaseTrackedAuthorOut } from "@/lib/api";

// ---------------------------------------------------------------------------
// Release date badge
// ---------------------------------------------------------------------------

function ReleaseDateBadge({ dateStr }: { dateStr: string | null }) {
  if (!dateStr) return <span className="text-xs text-text-secondary">TBD</span>;

  const releaseDate = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((releaseDate.getTime() - today.getTime()) / 86_400_000);

  if (diffDays <= 0)  return <Badge variant="positive">{dateStr}</Badge>;
  if (diffDays <= 30) return <Badge variant="warning">{dateStr}</Badge>;
  return <Badge variant="neutral">{dateStr}</Badge>;
}

// ---------------------------------------------------------------------------
// Releases tab — per-row inline edit
// ---------------------------------------------------------------------------

const AUTHOR_ALL = "__all__";

function ReleaseRow({ release }: { release: ReleaseOut }) {
  const [editing, setEditing] = useState(false);
  const [dateVal, setDateVal] = useState(release.release_date ?? "");
  const [notesVal, setNotesVal] = useState(release.notes ?? "");
  const [confirmedVal, setConfirmedVal] = useState(release.release_date_confirmed);
  const patch = usePatchRelease();

  function handleSave() {
    patch.mutate(
      {
        id: release.id,
        release_date_confirmed: confirmedVal,
        release_date: dateVal || null,
        notes: notesVal || null,
      },
      { onSuccess: () => setEditing(false) },
    );
  }

  function handleCancel() {
    setEditing(false);
    setDateVal(release.release_date ?? "");
    setNotesVal(release.notes ?? "");
    setConfirmedVal(release.release_date_confirmed);
  }

  return (
    <>
      <tr className="border-b border-border hover:bg-surface-hover transition-colors">
        <td className="py-3 px-4">
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary">
              {release.title}
              {release.book_number && (
                <span className="text-text-secondary ml-1">#{release.book_number}</span>
              )}
            </p>
            {release.link_url && (
              <a
                href={release.link_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-accent hover:underline"
              >
                View
              </a>
            )}
          </div>
        </td>
        <td className="py-3 px-4 text-sm text-text-primary">{release.author_name}</td>
        <td className="py-3 px-4">
          <div className="flex items-center gap-1.5">
            <ReleaseDateBadge dateStr={release.release_date} />
            {release.release_date_confirmed ? (
              <Check className="w-3 h-3 text-green-500 shrink-0" aria-label="Date confirmed" />
            ) : (
              <HelpCircle className="w-3 h-3 text-text-secondary opacity-40 shrink-0" aria-label="Date unconfirmed" />
            )}
          </div>
        </td>
        <td className="py-3 px-4">
          {release.source && <Badge variant="neutral">{release.source}</Badge>}
        </td>
        <td className="py-3 px-4">
          <button
            onClick={() => setEditing((e) => !e)}
            className="text-text-secondary hover:text-text-primary"
            title="Edit release"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
        </td>
      </tr>
      {editing && (
        <tr className="border-b border-border bg-surface">
          <td colSpan={5} className="px-4 py-3">
            <div className="flex flex-wrap gap-3 items-end">
              <div className="space-y-1">
                <label className="text-xs text-text-secondary">Release date</label>
                <Input
                  value={dateVal}
                  onChange={(e) => setDateVal(e.target.value)}
                  placeholder="YYYY or YYYY-MM-DD"
                  className="w-40"
                />
              </div>
              <div className="space-y-1 flex-1 min-w-[12rem]">
                <label className="text-xs text-text-secondary">Notes</label>
                <Input
                  value={notesVal}
                  onChange={(e) => setNotesVal(e.target.value)}
                  placeholder="Optional notes"
                />
              </div>
              <button
                onClick={() => setConfirmedVal((v) => !v)}
                className={cn(
                  "flex items-center gap-1 text-xs px-2 py-1.5 rounded-md border transition-colors",
                  confirmedVal
                    ? "border-green-500 text-green-500 bg-green-500/10"
                    : "border-border text-text-secondary hover:border-text-secondary",
                )}
              >
                <Check className="w-3 h-3" />
                {confirmedVal ? "Confirmed" : "Unconfirmed"}
              </button>
              <div className="flex items-center gap-3">
                <button
                  disabled={patch.isPending}
                  onClick={handleSave}
                  className="text-xs text-accent hover:text-accent/80 disabled:opacity-40"
                >
                  Save
                </button>
                <button
                  onClick={handleCancel}
                  className="text-xs text-text-secondary hover:text-text-primary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function ReleasesTab() {
  const [authorFilter, setAuthorFilter] = useState(AUTHOR_ALL);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [lastFailedCount, setLastFailedCount] = useState(0);

  const releases = useReleases(authorFilter !== AUTHOR_ALL ? authorFilter : undefined);
  const tracked  = useTrackedAuthors();
  const refresh  = useRefreshReleases();

  const authorOptions = [
    { value: AUTHOR_ALL, label: "All authors" },
    ...(tracked.data ?? []).map((a) => ({ value: a.name, label: a.name })),
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Select
          options={authorOptions}
          value={authorFilter}
          onValueChange={setAuthorFilter}
        />
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-xs text-text-secondary">
              Last refreshed: {lastRefreshed.toLocaleTimeString()}
              {lastFailedCount > 0 && (
                <span className="ml-2 text-red-400">({lastFailedCount} failed)</span>
              )}
            </span>
          )}
          <button
            disabled={refresh.isPending}
            onClick={() =>
              refresh.mutate(undefined, {
                onSuccess: (result) => {
                  setLastRefreshed(new Date());
                  setLastFailedCount(result.failed);
                },
              })
            }
            className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${refresh.isPending ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {releases.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : (releases.data?.length ?? 0) === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
          <BookMarked className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-lg font-medium text-text-primary">No upcoming releases</p>
          <p className="text-sm text-text-secondary">
            Track authors to see their upcoming releases here.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm overflow-auto">
            <thead>
              <tr className="border-b border-border">
                {["Title", "Author", "Release Date", "Source", ""].map((h) => (
                  <th key={h} className="py-3 px-4 text-left text-text-secondary font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {releases.data?.map((r) => <ReleaseRow key={r.id} release={r} />)}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tracked Authors tab — Add search
// ---------------------------------------------------------------------------

function AddAuthorSearch({ trackedNames }: { trackedNames: Set<string> }) {
  const [q, setQ] = useState("");
  const search = useSearchAuthors(q);
  const add    = useAddTrackedAuthor();

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
            const already = trackedNames.has(result.name);
            return (
              <div key={result.ol_key} className="flex items-center gap-3 px-4 py-3 bg-surface">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{result.name}</p>
                  {result.top_work && (
                    <p className="text-xs text-text-secondary line-clamp-1">{result.top_work}</p>
                  )}
                </div>
                <button
                  disabled={already || add.isPending}
                  onClick={() => {
                    add.mutate({ name: result.name, ol_key: result.ol_key });
                    setQ("");
                  }}
                  className="text-sm text-accent hover:text-accent/80 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
                >
                  {already ? "Tracking" : "Track"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tracked Authors tab — Author row
// ---------------------------------------------------------------------------

function TrackedAuthorRow({ author }: { author: ReleaseTrackedAuthorOut }) {
  const [confirming, setConfirming] = useState(false);
  const remove = useRemoveTrackedAuthor();

  return (
    <div className="flex items-center gap-3 px-4 py-3 hover:bg-surface-hover">
      <span className="text-sm text-text-primary flex-1">{author.name}</span>
      {confirming ? (
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-secondary">Remove?</span>
          <button
            className="text-xs text-red-500 hover:underline"
            onClick={() => {
              remove.mutate(author.id);
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
          disabled={remove.isPending}
          onClick={() => setConfirming(true)}
          className="flex items-center gap-1 text-xs text-text-secondary hover:text-red-500 disabled:opacity-40"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Remove
        </button>
      )}
    </div>
  );
}

function TrackedAuthorsTab() {
  const { data, isLoading } = useTrackedAuthors();
  const trackedNames = new Set((data ?? []).map((a) => a.name));

  return (
    <div className="space-y-6">
      <AddAuthorSearch trackedNames={trackedNames} />

      {isLoading ? (
        <div className="space-y-1">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-11 w-full rounded-lg" />
          ))}
        </div>
      ) : (data?.length ?? 0) === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <BookMarked className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-lg font-medium text-text-primary">No authors tracked</p>
          <p className="text-sm text-text-secondary">
            Use the search above to track authors for upcoming releases.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-border border border-border rounded-xl overflow-hidden">
          {data?.map((author) => (
            <TrackedAuthorRow key={author.id} author={author} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ReleasesPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-text-primary">Releases</h1>

      <Tabs.Root defaultValue="upcoming">
        <Tabs.List className="flex gap-1 bg-surface rounded-lg p-1 w-fit">
          <Tabs.Trigger
            value="upcoming"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            Upcoming
          </Tabs.Trigger>
          <Tabs.Trigger
            value="tracked"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            Tracked Authors
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="upcoming" className="mt-6">
          <ReleasesTab />
        </Tabs.Content>

        <Tabs.Content value="tracked" className="mt-6">
          <TrackedAuthorsTab />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
