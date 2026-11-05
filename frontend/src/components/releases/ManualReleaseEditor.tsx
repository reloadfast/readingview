import { useState } from "react";
import { Button, Input, Select } from "@/components/ui";
import {
  useCreateManualRelease,
  useUpdateManualRelease,
  useUploadManualReleaseCover,
} from "@/hooks/useReleases";
import type { ManualRelease, ManualReleaseInput, ManualReleaseMedium } from "@/lib/api";

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

export function ManualReleaseEditor({
  entry,
  initialValues,
  imported = false,
  onMediaChange,
  onDone,
}: {
  entry?: ManualRelease;
  initialValues?: ManualReleaseInput;
  imported?: boolean;
  onMediaChange?: (media: ManualReleaseMedium[]) => void;
  onDone: () => void;
}) {
  const [values, setValues] = useState<ManualReleaseInput>(
    () => initialValues ?? manualInput(entry)
  );
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
    const media = values.media ?? [];
    const next = media.includes(medium)
      ? media.filter((item) => item !== medium)
      : [...media, medium];
    setValues((current) => ({ ...current, media: next }));
    onMediaChange?.(next);
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
        <Input
          aria-label="Author"
          value={values.author ?? ""}
          onChange={(e) => setText("author", e.target.value)}
          placeholder="Author"
        />
        <Input
          aria-label="Book title"
          value={values.title ?? ""}
          onChange={(e) => setText("title", e.target.value)}
          placeholder="Book title"
        />
        <Input
          aria-label="Series"
          value={values.series ?? ""}
          onChange={(e) => setText("series", e.target.value)}
          placeholder="Series"
        />
        <Input
          aria-label="Series number"
          type="number"
          step="any"
          value={values.series_number ?? ""}
          onChange={(e) => setSeriesNumber(e.target.value)}
          placeholder="Series number"
        />
        <Input
          aria-label="Release date"
          value={values.release_date ?? ""}
          onChange={(e) => setText("release_date", e.target.value)}
          placeholder="Release date (YYYY or YYYY-MM-DD)"
          pattern="\\d{4}(-\\d{2}-\\d{2})?"
          title="Use YYYY or YYYY-MM-DD"
        />
        <Input
          aria-label="Cover image URL"
          value={values.cover_url ?? ""}
          onChange={(e) => setText("cover_url", e.target.value)}
          placeholder="Cover image URL"
        />
        <Input
          aria-label="Relevant link"
          value={values.link_url ?? ""}
          onChange={(e) => setText("link_url", e.target.value)}
          placeholder="Relevant link"
        />
      </div>
      <textarea
        aria-label="Comments"
        value={values.comments ?? ""}
        onChange={(e) => setText("comments", e.target.value)}
        placeholder="Comments"
        className="min-h-20 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent"
      />
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="text-xs text-text-secondary">Medium</span>
        {MEDIUMS.map((medium) => (
          <label
            key={medium.value}
            className="flex items-center gap-1.5 text-sm text-text-secondary"
          >
            <input
              type="checkbox"
              checked={(values.media ?? []).includes(medium.value)}
              onChange={() => toggleMedium(medium.value)}
            />
            {medium.label}
          </label>
        ))}
        <Select
          className="ml-auto"
          value={values.status ?? "watching"}
          onValueChange={(status) =>
            setValues((current) => ({ ...current, status: status as ManualRelease["status"] }))
          }
          options={[
            { value: "watching", label: "Watching" },
            { value: "released", label: "Released" },
            { value: "owned", label: "Owned" },
          ]}
        />
      </div>
      {imported && (
        <p className="text-sm text-text-secondary">
          The date belongs to the linked edition. If you change the medium, verify the release date.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-text-secondary">
          <span className="mr-2">Upload cover</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            onChange={(e) => setCoverFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <button
          onClick={() => setValues((current) => ({ ...current, last_checked_at: Date.now() }))}
          className="text-xs text-accent hover:underline"
        >
          Mark checked today
        </button>
        {values.last_checked_at && (
          <span className="text-xs text-text-secondary">
            Checked {new Date(values.last_checked_at).toLocaleDateString()}
          </span>
        )}
        <div className="ml-auto flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone}>
            Cancel
          </Button>
          <Button size="sm" disabled={pending} onClick={() => void save()} pendingText="Saving…">
            Save
          </Button>
        </div>
      </div>
      {error instanceof Error && (
        <p role="alert" className="text-sm text-red-400">
          {error.message}
        </p>
      )}
      <p className="text-xs text-text-secondary">
        Duplicates are blocked by author, title, release date, and medium.
      </p>
    </div>
  );
}
