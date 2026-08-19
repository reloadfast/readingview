import { useState } from "react";
import { Archive, BookMarked, Check, Copy, Download, EyeOff, HelpCircle, Pencil, Plus, RefreshCw, Search, Trash2 } from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { Badge, Button, Input, Select, Skeleton } from "@/components/ui";
import {
  useAddTrackedAuthor,
  useCreateManualRelease,
  useManualReleases,
  usePatchRelease,
  useRefreshReleases,
  useReleases,
  useRemoveTrackedAuthor,
  useTrackedAuthors,
  useUpdateManualRelease,
  useUploadManualReleaseCover,
} from "@/hooks/useReleases";
import { useSearchAuthors } from "@/hooks/useAuthors";
import { cn } from "@/lib/utils";
import type {
  ManualRelease,
  ManualReleaseInput,
  ManualReleaseMedium,
  ReleaseOut,
  TrackedAuthorOut,
} from "@/lib/api";

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

  function handleVisibility() {
    patch.mutate({ id: release.id, is_active: !release.is_active });
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
          <div className="flex items-center gap-2">
            <button
              disabled={patch.isPending}
              onClick={handleVisibility}
              className="text-text-secondary hover:text-text-primary disabled:opacity-40"
              title={release.is_active ? "Not interested — hide release" : "Restore release"}
            >
              <EyeOff className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setEditing((e) => !e)}
              className="text-text-secondary hover:text-text-primary"
              title="Edit release"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          </div>
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
  const [includeManual, setIncludeManual] = useState(true);
  const [showHidden, setShowHidden] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [lastFailedCount, setLastFailedCount] = useState(0);
  const [calendarCopied, setCalendarCopied] = useState(false);

  const releases = useReleases(authorFilter !== AUTHOR_ALL ? authorFilter : undefined, showHidden);
  const tracked  = useTrackedAuthors();
  const refresh  = useRefreshReleases();
  const manual = useManualReleases();

  const authorOptions = [
    { value: AUTHOR_ALL, label: "All authors" },
    ...(tracked.data ?? []).map((a) => ({ value: a.name, label: a.name })),
  ];

  const copyCalendarUrl = async () => {
    const url = new URL("/api/releases/calendar.ics", window.location.origin).toString();
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      const input = document.createElement("textarea");
      input.value = url;
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.append(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }
    setCalendarCopied(true);
    window.setTimeout(() => setCalendarCopied(false), 2_000);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Select
          options={authorOptions}
          value={authorFilter}
          onValueChange={setAuthorFilter}
        />
        <div className="flex items-center gap-3">
          <a
            href="/api/releases/calendar.ics"
            download="readingview-releases.ics"
            className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
            title="Download calendar"
          >
            <Download className="w-4 h-4" />
            Calendar
          </a>
          <button
            onClick={() => void copyCalendarUrl()}
            className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
            title="Copy calendar feed URL"
          >
            <Copy className="w-4 h-4" />
            {calendarCopied ? "Copied" : "Copy feed"}
          </button>
          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={includeManual}
              onChange={(event) => setIncludeManual(event.target.checked)}
              className="accent-[var(--color-accent)]"
            />
            Include manual tracking
          </label>
          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={showHidden}
              onChange={(event) => setShowHidden(event.target.checked)}
              className="accent-[var(--color-accent)]"
            />
            Show hidden
          </label>
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
      {includeManual && (manual.data?.length ?? 0) > 0 && (
        <div className="rounded-xl border border-border overflow-hidden">
          <div className="px-4 py-2 border-b border-border text-xs text-text-secondary">
            Manual tracking
          </div>
          <div className="divide-y divide-border">
            {manual.data?.filter((entry) => entry.status === "watching").map((entry) => (
              <div key={entry.id} className="flex items-center gap-3 px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{entry.title || "Untitled release"}</p>
                  <p className="text-xs text-text-secondary">{entry.author || "Unknown author"}</p>
                </div>
                <ReleaseDateBadge dateStr={entry.release_date} />
                <Badge variant="neutral">{entry.status}</Badge>
              </div>
            ))}
          </div>
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

function TrackedAuthorRow({ author }: { author: TrackedAuthorOut }) {
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
// Manual tracking
// ---------------------------------------------------------------------------

const MEDIUMS: { value: ManualReleaseMedium; label: string }[] = [
  { value: "audiobook", label: "Audiobook" },
  { value: "ebook", label: "Ebook" },
  { value: "hardcover", label: "Hardcover" },
  { value: "paperback", label: "Paperback" },
];

function manualInput(entry?: ManualRelease): ManualReleaseInput {
  if (!entry) return { media: [], status: "watching" };
  return {
    author: entry.author,
    title: entry.title,
    series: entry.series,
    series_number: entry.series_number,
    release_date: entry.release_date,
    media: entry.media,
    cover_url: entry.cover_url,
    link_url: entry.link_url,
    comments: entry.comments,
    last_checked_at: entry.last_checked_at,
    status: entry.status,
  };
}

function ManualReleaseEditor({
  entry,
  onDone,
}: {
  entry?: ManualRelease;
  onDone: () => void;
}) {
  const [values, setValues] = useState<ManualReleaseInput>(() => manualInput(entry));
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const create = useCreateManualRelease();
  const update = useUpdateManualRelease();
  const upload = useUploadManualReleaseCover();
  const pending = create.isPending || update.isPending || upload.isPending;
  const error = create.error || update.error || upload.error;

  function setText(field: keyof ManualReleaseInput, value: string) {
    setValues((current) => ({ ...current, [field]: value || null }));
  }

  function setSeriesNumber(value: string) {
    setValues((current) => ({
      ...current,
      series_number: value === "" ? null : Number(value),
    }));
  }

  function toggleMedium(medium: ManualReleaseMedium) {
    setValues((current) => {
      const media = current.media ?? [];
      return {
        ...current,
        media: media.includes(medium) ? media.filter((item) => item !== medium) : [...media, medium],
      };
    });
  }

  async function save() {
    try {
      const { last_checked_at, ...releaseValues } = values;
      const payload = entry && last_checked_at === entry.last_checked_at ? releaseValues : values;
      const saved = entry
        ? await update.mutateAsync({ id: entry.id, ...payload })
        : await create.mutateAsync(payload);
      if (coverFile) await upload.mutateAsync({ id: saved.id, file: coverFile });
      onDone();
    } catch {
      // Mutation error is displayed below.
    }
  }

  return (
    <div className="space-y-4 rounded-xl border border-border bg-surface p-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Input value={values.author ?? ""} onChange={(e) => setText("author", e.target.value)} placeholder="Author" />
        <Input value={values.title ?? ""} onChange={(e) => setText("title", e.target.value)} placeholder="Book title" />
        <Input value={values.series ?? ""} onChange={(e) => setText("series", e.target.value)} placeholder="Series" />
        <Input type="number" step="any" value={values.series_number ?? ""} onChange={(e) => setSeriesNumber(e.target.value)} placeholder="Series number" />
        <Input value={values.release_date ?? ""} onChange={(e) => setText("release_date", e.target.value)} placeholder="Release date (YYYY-MM-DD)" />
        <Input value={values.cover_url ?? ""} onChange={(e) => setText("cover_url", e.target.value)} placeholder="Cover image URL" />
        <Input value={values.link_url ?? ""} onChange={(e) => setText("link_url", e.target.value)} placeholder="Relevant link" />
      </div>
      <textarea
        value={values.comments ?? ""}
        onChange={(e) => setText("comments", e.target.value)}
        placeholder="Comments"
        className="min-h-20 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent"
      />
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="text-xs text-text-secondary">Medium</span>
        {MEDIUMS.map((medium) => (
          <label key={medium.value} className="flex items-center gap-1.5 text-sm text-text-secondary">
            <input type="checkbox" checked={(values.media ?? []).includes(medium.value)} onChange={() => toggleMedium(medium.value)} />
            {medium.label}
          </label>
        ))}
        <Select
          className="ml-auto"
          value={values.status ?? "watching"}
          onValueChange={(status) => setValues((current) => ({ ...current, status: status as ManualRelease["status"] }))}
          options={[
            { value: "watching", label: "Watching" },
            { value: "released", label: "Released" },
            { value: "owned", label: "Owned" },
          ]}
        />
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-text-secondary">
          <span className="mr-2">Upload cover</span>
          <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={(e) => setCoverFile(e.target.files?.[0] ?? null)} />
        </label>
        <button
          onClick={() => setValues((current) => ({ ...current, last_checked_at: Date.now() }))}
          className="text-xs text-accent hover:underline"
        >
          Mark checked today
        </button>
        {values.last_checked_at && <span className="text-xs text-text-secondary">Checked {new Date(values.last_checked_at).toLocaleDateString()}</span>}
        <div className="ml-auto flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone}>Cancel</Button>
          <Button size="sm" disabled={pending} onClick={() => void save()} pendingText="Saving…">
            Save
          </Button>
        </div>
      </div>
      {error instanceof Error && <p className="text-sm text-red-400">{error.message}</p>}
      <p className="text-xs text-text-secondary">Duplicates are blocked by author, title, release date, and medium.</p>
    </div>
  );
}

function ManualReleaseRow({ entry }: { entry: ManualRelease }) {
  const [editing, setEditing] = useState(false);
  const update = useUpdateManualRelease();
  const cover = entry.uploaded_cover_url ?? entry.cover_url;
  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <div className="flex gap-3 p-3">
        {cover ? <img src={cover} alt="" className="h-16 w-12 rounded object-contain bg-background" /> : <div className="h-16 w-12 rounded bg-background" />}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-text-primary">{entry.title || "Untitled release"}</p>
            <Badge variant="neutral">{entry.status}</Badge>
            {entry.media.map((medium) => <Badge key={medium} variant="neutral">{medium}</Badge>)}
          </div>
          <p className="text-sm text-text-secondary">{entry.author || "Unknown author"}{entry.series ? ` · ${entry.series}${entry.series_number != null ? ` #${entry.series_number}` : ""}` : ""}</p>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-text-secondary">
            <ReleaseDateBadge dateStr={entry.release_date} />
            {entry.last_checked_at && <span>Checked {new Date(entry.last_checked_at).toLocaleDateString()}</span>}
            {entry.link_url && <a className="text-accent hover:underline" href={entry.link_url} target="_blank" rel="noopener noreferrer">Link</a>}
          </div>
        </div>
        <div className="flex items-start gap-2">
          <Button variant="ghost" size="sm" onClick={() => setEditing((current) => !current)}><Pencil className="h-3.5 w-3.5" /></Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={update.isPending}
            onClick={() => update.mutate({ id: entry.id, archived: !entry.archived })}
            title={entry.archived ? "Restore" : "Archive"}
          >
            <Archive className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
      {entry.comments && !editing && <p className="px-3 pb-3 text-sm text-text-secondary whitespace-pre-wrap">{entry.comments}</p>}
      {editing && <div className="border-t border-border p-3"><ManualReleaseEditor entry={entry} onDone={() => setEditing(false)} /></div>}
    </div>
  );
}

function ManualTrackingTab() {
  const [adding, setAdding] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const releases = useManualReleases(showArchived);
  const visible = (releases.data ?? []).filter(
    (entry) =>
      (showArchived || !entry.archived) &&
      (showArchived || showHistory || entry.status === "watching"),
  );
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap gap-3">
          <label className="flex items-center gap-2 text-sm text-text-secondary"><input type="checkbox" checked={showHistory} onChange={(e) => setShowHistory(e.target.checked)} /> Show released &amp; owned</label>
          <label className="flex items-center gap-2 text-sm text-text-secondary"><input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} /> Show archived</label>
        </div>
        <Button size="sm" onClick={() => setAdding(true)}><Plus className="mr-1 h-4 w-4" />Add release</Button>
      </div>
      {adding && <ManualReleaseEditor onDone={() => setAdding(false)} />}
      {releases.isLoading ? <Skeleton className="h-40 w-full rounded-xl" /> : visible.length === 0 ? (
        <div className="py-16 text-center text-sm text-text-secondary">No manual releases yet. Add anything you want to keep an eye on.</div>
      ) : <div className="space-y-3">{visible.map((entry) => <ManualReleaseRow key={entry.id} entry={entry} />)}</div>}
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
          <Tabs.Trigger
            value="manual"
            className="px-4 py-1.5 text-sm rounded-md text-text-secondary transition-colors data-[state=active]:bg-surface-hover data-[state=active]:text-text-primary"
          >
            Manual Tracking
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="upcoming" className="mt-6">
          <ReleasesTab />
        </Tabs.Content>

        <Tabs.Content value="tracked" className="mt-6">
          <TrackedAuthorsTab />
        </Tabs.Content>
        <Tabs.Content value="manual" className="mt-6">
          <ManualTrackingTab />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
