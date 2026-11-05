import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { GoodreadsLookupResult } from "@/lib/api";
import { ReleaseCreation } from "./ReleaseCreation";

const source = "https://www.goodreads.com/book/show/257149406";
const result: GoodreadsLookupResult = {
  status: "ok",
  source_url: source,
  draft: {
    title: "Bog Standard Isekai: Towering - A LitRPG Isekai Adventure",
    author: "Miles English",
    series: "Bog Standard Isekai",
    series_number: 6,
    release_date: "2027-08-17",
    media: ["ebook"],
    cover_url: "https://example.org/cover.jpg",
    link_url: source,
    status: "watching",
  },
  sources: { title: "next_data", media: "json_ld", release_date: "next_data" },
  missing_fields: [],
  warnings: ["Review this edition before saving."],
  existing_releases: [],
};
function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
const fetchMock = vi.fn<typeof fetch>();
function requestAt(index: number) {
  const call = fetchMock.mock.calls[index];
  if (!call || !call[1]) throw new Error("Expected a request with options");
  return { url: call[0], options: call[1] };
}
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const done = vi.fn();
  const viewExisting = vi.fn();
  render(
    <QueryClientProvider client={client}>
      <ReleaseCreation onDone={done} onViewExisting={viewExisting} />
    </QueryClientProvider>
  );
  return { done, invalidate, viewExisting };
}
function chooseGoodreads() {
  fireEvent.click(screen.getByRole("button", { name: "From Goodreads" }));
  fireEvent.change(screen.getByLabelText("Goodreads book URL"), { target: { value: source } });
}
async function importDraft() {
  chooseGoodreads();
  fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
  await screen.findByLabelText("Book title");
}
beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("release creation", () => {
  it("shows multiple matching entries and navigates to the selected one without discarding edits", async () => {
    const matches = [
      {
        id: 1,
        title: "Ebook copy",
        author: "Miles English",
        release_date: "2027-08-17",
        media: ["ebook"],
        status: "owned",
        archived: false,
      },
      {
        id: 2,
        title: "Archived copy",
        author: null,
        release_date: null,
        media: [],
        status: "released",
        archived: true,
      },
    ];
    fetchMock.mockResolvedValueOnce(response({ ...result, existing_releases: matches }));
    const { viewExisting, done } = setup();
    await importDraft();
    const warning = screen.getByRole("region", {
      name: "Existing releases for this Goodreads book",
    });
    expect(within(warning).getByText("Same medium")).toBeInTheDocument();
    expect(within(warning).getByText("Medium unspecified")).toBeInTheDocument();
    expect(within(warning).getByText("Archived")).toBeInTheDocument();
    expect(within(warning).getByText("Unknown author")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Book title"), { target: { value: "My draft" } });
    fireEvent.click(within(warning).getByRole("button", { name: /View existing: Archived copy/ }));
    expect(viewExisting).toHaveBeenCalledWith(matches[1]);
    expect(done).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Book title")).toHaveValue("My draft");
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("keeps manual addition blank and saves only on explicit Save", async () => {
    const { done } = setup();
    fireEvent.click(screen.getByRole("button", { name: "Manual" }));
    expect(screen.getByLabelText("Book title")).toHaveValue("");
    expect(screen.getByLabelText("Relevant link")).toHaveValue("");
    expect(fetchMock).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Book title"), { target: { value: "Manual title" } });
    fetchMock.mockResolvedValueOnce(response({ id: 1 }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(done).toHaveBeenCalledOnce());
    expect(requestAt(0).url).toBe("/api/releases/manual");
    expect(JSON.parse(requestAt(0).options.body as string).title).toBe("Manual title");
  });
  it("imports editable details and saves corrections without inferring an audiobook date", async () => {
    fetchMock.mockResolvedValueOnce(response(result));
    const { done, invalidate } = setup();
    await importDraft();
    expect(screen.getByLabelText("Book title")).toHaveValue(result.draft.title);
    expect(screen.getByLabelText("Author")).toHaveValue("Miles English");
    expect(screen.getByLabelText("Series")).toHaveValue("Bog Standard Isekai");
    expect(screen.getByLabelText("Series number")).toHaveValue(6);
    expect(screen.getByLabelText("Release date")).toHaveValue("2027-08-17");
    expect(screen.getByRole("checkbox", { name: "Ebook" })).toBeChecked();
    expect(screen.getByLabelText("Comments")).toHaveValue("");
    expect(screen.getByRole("link", { name: "Source on Goodreads" })).toHaveAttribute(
      "href",
      source
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(invalidate).not.toHaveBeenCalled();
    expect(requestAt(0).url).toBe("/api/releases/manual/lookup-goodreads");
    expect(JSON.parse(requestAt(0).options.body as string)).toEqual({ url: source });
    fireEvent.change(screen.getByLabelText("Book title"), { target: { value: "Towering" } });
    fireEvent.click(screen.getByRole("checkbox", { name: "Ebook" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Audiobook" }));
    expect(screen.getByLabelText("Release date")).toHaveValue("2027-08-17");
    expect(
      screen.getByText(/If you change the medium, verify the release date/)
    ).toBeInTheDocument();
    fetchMock.mockResolvedValueOnce(response({ id: 1 }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(done).toHaveBeenCalledOnce());
    expect(JSON.parse(requestAt(1).options.body as string)).toMatchObject({
      title: "Towering",
      media: ["audiobook"],
      release_date: "2027-08-17",
      link_url: source,
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["manual-releases"] });
  });
  it("leaves missing details blank and displays partial-result warnings", async () => {
    fetchMock.mockResolvedValueOnce(
      response({
        ...result,
        status: "partial",
        draft: {
          ...result.draft,
          author: null,
          series: null,
          series_number: null,
          release_date: null,
          media: [],
        },
        warnings: ["Publication date is uncertain."],
      })
    );
    setup();
    await importDraft();
    expect(screen.getByLabelText("Author")).toHaveValue("");
    expect(screen.getByLabelText("Release date")).toHaveValue("");
    expect(screen.getByRole("checkbox", { name: "Ebook" })).not.toBeChecked();
    expect(screen.getByText(/Some details were unavailable/)).toBeInTheDocument();
    expect(screen.getByText("Publication date is uncertain.")).toBeInTheDocument();
  });
  it("rejects invalid URLs without fetching", async () => {
    setup();
    chooseGoodreads();
    fireEvent.change(screen.getByLabelText("Goodreads book URL"), {
      target: { value: "https://goodreads.com.evil.test/book/show/123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Use an HTTPS Goodreads book URL");
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("retains the URL after failure and retries only when requested", async () => {
    fetchMock.mockResolvedValueOnce(
      response({ detail: "Goodreads blocked access. Add the release manually." }, 502)
    );
    setup();
    chooseGoodreads();
    fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Goodreads blocked access");
    expect(screen.getByLabelText("Goodreads book URL")).toHaveValue(source);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fetchMock.mockResolvedValueOnce(response(result));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByLabelText("Book title")).toHaveValue(result.draft.title);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
  it("supports manual fallback with only the supplied link after failure", async () => {
    fetchMock.mockRejectedValueOnce(new Error("Network unavailable"));
    setup();
    chooseGoodreads();
    fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Enter manually" }));
    expect(screen.getByLabelText("Relevant link")).toHaveValue(source);
    expect(screen.getByLabelText("Book title")).toHaveValue("");
    expect(screen.getByLabelText("Author")).toHaveValue("");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("preserves corrections when saving fails", async () => {
    fetchMock.mockResolvedValueOnce(response(result));
    const { done } = setup();
    await importDraft();
    fireEvent.change(screen.getByLabelText("Book title"), {
      target: { value: "My corrected title" },
    });
    fetchMock.mockResolvedValueOnce(response({ detail: "An exact duplicate already exists" }, 409));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("An exact duplicate already exists");
    expect(screen.getByLabelText("Book title")).toHaveValue("My corrected title");
    expect(done).not.toHaveBeenCalled();
  });
  it("aborts pending lookup on manual fallback and ignores late results", async () => {
    let finish!: (value: Response) => void;
    fetchMock.mockReturnValueOnce(
      new Promise<Response>((resolve) => {
        finish = resolve;
      })
    );
    setup();
    chooseGoodreads();
    fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
    expect(await screen.findByRole("button", { name: "Fetching details…" })).toBeDisabled();
    expect(screen.getByLabelText("Goodreads book URL")).toBeDisabled();
    const signal = requestAt(0).options.signal;
    fireEvent.click(screen.getByRole("button", { name: "Enter manually" }));
    fireEvent.change(screen.getByLabelText("Book title"), {
      target: { value: "Manual correction" },
    });
    expect(signal?.aborted).toBe(true);
    await act(async () => {
      finish(response(result));
    });
    expect(screen.getByLabelText("Book title")).toHaveValue("Manual correction");
    expect(screen.queryByRole("link", { name: "Source on Goodreads" })).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("does not reopen canceled creation after a late result", async () => {
    let finish!: (value: Response) => void;
    fetchMock.mockReturnValueOnce(
      new Promise<Response>((resolve) => {
        finish = resolve;
      })
    );
    const client = new QueryClient();
    function Host() {
      const [open, setOpen] = useState(true);
      return open ? (
        <ReleaseCreation onDone={() => setOpen(false)} onViewExisting={() => {}} />
      ) : (
        <p>Closed</p>
      );
    }
    render(
      <QueryClientProvider client={client}>
        <Host />
      </QueryClientProvider>
    );
    chooseGoodreads();
    fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
    await screen.findByRole("button", { name: "Fetching details…" });
    const signal = requestAt(0).options.signal;
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(signal?.aborted).toBe(true);
    await act(async () => {
      finish(response(result));
    });
    expect(screen.getByText("Closed")).toBeInTheDocument();
    expect(screen.queryByLabelText("Book title")).not.toBeInTheDocument();
  });
});
