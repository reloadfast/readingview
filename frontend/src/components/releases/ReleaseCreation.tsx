import { useEffect, useId, useRef, useState } from "react";
import { Badge, Button, Input } from "@/components/ui";
import { useLookupGoodreadsRelease } from "@/hooks/useReleases";
import type {
  GoodreadsExistingRelease,
  GoodreadsLookupResult,
  ManualReleaseInput,
  ManualReleaseMedium,
} from "@/lib/api";
import { ManualReleaseEditor } from "./ManualReleaseEditor";

export function ReleaseCreation({
  onDone,
  onViewExisting,
}: {
  onDone: () => void;
  onViewExisting: (entry: GoodreadsExistingRelease) => void;
}) {
  const [mode, setMode] = useState<"choose" | "manual" | "goodreads" | "review">("choose");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GoodreadsLookupResult | null>(null);
  const [draftMedia, setDraftMedia] = useState<ManualReleaseMedium[]>([]);
  const [manualDraft, setManualDraft] = useState<ManualReleaseInput>({
    media: [],
    status: "watching",
  });
  const lookup = useLookupGoodreadsRelease();
  const request = useRef<AbortController | null>(null);
  const inputId = useId();

  useEffect(() => () => request.current?.abort(), []);

  function stopLookup() {
    const active = request.current;
    request.current = null;
    active?.abort();
  }

  function cancel() {
    stopLookup();
    onDone();
  }

  function enterManually() {
    stopLookup();
    setManualDraft({ media: [], status: "watching", link_url: url.trim() || null });
    setMode("manual");
  }

  async function fetchDetails() {
    if (request.current) return;
    setError(null);
    try {
      const parsed = new URL(url.trim());
      if (
        url.trim().length > 2048 ||
        parsed.protocol !== "https:" ||
        !["goodreads.com", "www.goodreads.com"].includes(parsed.hostname) ||
        parsed.username ||
        parsed.password ||
        parsed.port ||
        !/^\/book\/show\/\d+(?:[-.][^/]+)?\/?$/.test(parsed.pathname)
      )
        throw new Error("Invalid Goodreads URL");
    } catch {
      setError("Use an HTTPS Goodreads book URL, such as https://www.goodreads.com/book/show/123.");
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    try {
      const response = await lookup.mutateAsync({ url: url.trim(), signal: controller.signal });
      if (request.current !== controller || controller.signal.aborted) return;
      setResult(response);
      setDraftMedia(response.draft.media);
      setMode("review");
    } catch (cause) {
      if (request.current !== controller || controller.signal.aborted) return;
      setError(cause instanceof Error ? cause.message : "Could not read Goodreads. Try again.");
    } finally {
      if (request.current === controller) request.current = null;
    }
  }

  if (mode === "manual") {
    return <ManualReleaseEditor initialValues={manualDraft} onDone={cancel} />;
  }

  if (mode === "review" && result) {
    return (
      <div className="space-y-3">
        <div className="space-y-2 rounded-xl border border-border bg-surface p-4">
          <p className="text-sm text-text-primary">Review the imported details before saving.</p>
          <a
            href={result.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-accent hover:underline"
          >
            Source on Goodreads
          </a>
          {result.warnings.length > 0 && (
            <ul className="list-disc space-y-1 pl-5 text-sm text-text-secondary">
              {result.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          )}
          {result.status === "partial" && (
            <p className="text-sm text-text-secondary">
              Some details were unavailable. You can fill in the remaining fields below.
            </p>
          )}
        </div>
        {result.existing_releases.length > 0 && (
          <section
            aria-label="Existing releases for this Goodreads book"
            className="space-y-3 rounded-xl border border-border bg-surface p-4"
          >
            <p role="status" className="text-sm text-text-primary">
              This Goodreads book is already tracked. You can view an existing entry or continue
              adding a release for another medium.
            </p>
            <ul className="space-y-3">
              {result.existing_releases.map((entry) => (
                <li key={entry.id} className="flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-text-primary">
                      {entry.title || "Untitled release"}
                    </p>
                    <p className="text-sm text-text-secondary">
                      {entry.author || "Unknown author"}
                    </p>
                    {entry.release_date && (
                      <p className="text-xs text-text-secondary">
                        Release date: {entry.release_date}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {entry.media.map((medium) => (
                        <Badge key={medium}>{medium}</Badge>
                      ))}
                      <Badge>{entry.status}</Badge>
                      {entry.archived && <Badge>Archived</Badge>}
                      <Badge
                        variant={
                          entry.media.some((medium) => draftMedia.includes(medium))
                            ? "warning"
                            : "neutral"
                        }
                      >
                        {entry.media.length === 0
                          ? "Medium unspecified"
                          : draftMedia.length === 0
                            ? "Choose a medium to compare"
                            : entry.media.some((medium) => draftMedia.includes(medium))
                              ? "Same medium"
                              : "Different medium"}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewExisting(entry)}
                    aria-label={`View existing: ${entry.title || "Untitled release"} (${entry.media.join(", ") || "unspecified medium"}, ${entry.status}${entry.archived ? ", archived" : ""})`}
                  >
                    View existing
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        )}
        <ManualReleaseEditor
          initialValues={result.draft}
          imported
          onMediaChange={setDraftMedia}
          onDone={cancel}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border border-border bg-surface p-4">
      {mode === "choose" ? (
        <>
          <p className="text-sm text-text-primary">How would you like to add this release?</p>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setMode("manual")}>
              Manual
            </Button>
            <Button onClick={() => setMode("goodreads")}>From Goodreads</Button>
            <Button variant="ghost" onClick={cancel}>
              Cancel
            </Button>
          </div>
        </>
      ) : (
        <form
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void fetchDetails();
          }}
          className="space-y-3"
          aria-busy={lookup.isPending}
        >
          <label htmlFor={inputId} className="text-sm text-text-primary">
            Goodreads book URL
          </label>
          <Input
            id={inputId}
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://www.goodreads.com/book/show/..."
            disabled={lookup.isPending}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
          />
          {error && (
            <p id={`${inputId}-error`} role="alert" className="text-sm text-red-400">
              {error}
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={lookup.isPending} pendingText="Fetching details…">
              {error ? "Retry" : "Fetch details"}
            </Button>
            <Button type="button" variant="outline" onClick={enterManually}>
              Enter manually
            </Button>
            <Button type="button" variant="ghost" onClick={cancel}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
