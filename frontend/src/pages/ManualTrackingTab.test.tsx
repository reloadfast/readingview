import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { GoodreadsLookupResult, ManualRelease, ManualReleaseStatus } from "@/lib/api";
import { ManualTrackingTab } from "./ReleasesPage";

const source = "https://www.goodreads.com/book/show/257149406";
const fetchMock = vi.fn<typeof fetch>();
const scroll = vi.fn();
const originalScroll = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollIntoView");
function response(value: unknown) {
  return new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } });
}
function existing(status: ManualReleaseStatus, archived: boolean): ManualRelease {
  return {
    id: 42,
    title: "Already tracked",
    author: "An author",
    series: null,
    series_number: null,
    release_date: "2027-08-17",
    media: ["ebook"],
    cover_url: null,
    uploaded_cover_url: null,
    link_url: source,
    comments: "Existing notes",
    last_checked_at: 1,
    updated_at: 1,
    status,
    archived,
  };
}
function lookup(entry: ManualRelease): GoodreadsLookupResult {
  return {
    status: "partial",
    source_url: source,
    draft: {
      title: "Imported title",
      author: "An author",
      series: null,
      series_number: null,
      release_date: "2027-08-17",
      media: ["ebook"],
      cover_url: null,
      link_url: source,
      status: "watching",
    },
    sources: {},
    missing_fields: ["series", "series_number"],
    warnings: [],
    existing_releases: [entry],
  };
}
function setup(
  entry: ManualRelease,
  options: { unavailable?: boolean; failArchiveLoad?: boolean } = {}
) {
  let archiveLoads = 0;
  fetchMock.mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("lookup-goodreads")) return response(lookup(entry));
    if (init?.method === "POST") return response({ id: 99 });
    if (url.includes("include_archived=true")) {
      archiveLoads++;
      if (options.failArchiveLoad && archiveLoads === 1) throw new Error("Network unavailable");
      return response(options.unavailable ? [] : [entry]);
    }
    return response(entry.archived || options.unavailable ? [] : [entry]);
  });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  render(
    <QueryClientProvider client={client}>
      <ManualTrackingTab />
    </QueryClientProvider>
  );
  return client;
}
async function importDraft() {
  fireEvent.click(screen.getByRole("button", { name: "Add release" }));
  fireEvent.click(screen.getByRole("button", { name: "From Goodreads" }));
  fireEvent.change(screen.getByLabelText("Goodreads book URL"), { target: { value: source } });
  fireEvent.click(screen.getByRole("button", { name: "Fetch details" }));
  await screen.findByLabelText("Book title");
}
beforeEach(() => {
  fetchMock.mockReset();
  scroll.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
    configurable: true,
    value: scroll,
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  if (originalScroll)
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", originalScroll);
  else Reflect.deleteProperty(HTMLElement.prototype, "scrollIntoView");
});

describe("View existing navigation", () => {
  it.each([
    ["watching", false],
    ["owned", false],
    ["released", false],
    ["watching", true],
    ["owned", true],
  ] as const)(
    "reveals and focuses a %s release (archived: %s) without changing it",
    async (status, archived) => {
      const entry = existing(status, archived);
      setup(entry);
      await importDraft();
      fireEvent.change(screen.getByLabelText("Book title"), {
        target: { value: "My draft correction" },
      });
      const warning = screen.getByRole("region", {
        name: "Existing releases for this Goodreads book",
      });
      expect(within(warning).getByText(status)).toBeInTheDocument();
      if (archived) expect(within(warning).getByText("Archived")).toBeInTheDocument();
      fireEvent.click(within(warning).getByRole("button", { name: /^View existing:/ }));
      const row = await screen.findByRole("article", { name: "Release: Already tracked" });
      await waitFor(() => expect(row).toHaveFocus());
      expect(scroll).toHaveBeenCalledWith({ block: "center" });
      expect(row).toHaveClass("ring-2");
      expect(within(row).getByText(status)).toBeInTheDocument();
      expect(within(row).getByText("Existing notes")).toBeInTheDocument();
      expect(screen.getByLabelText("Book title")).toHaveValue("My draft correction");
      expect(screen.getByRole("checkbox", { name: "Show archived" })).toHaveProperty(
        "checked",
        archived
      );
      expect(screen.getByRole("checkbox", { name: "Show released & owned" })).toHaveProperty(
        "checked",
        status !== "watching"
      );
      expect(
        fetchMock.mock.calls.every(([, init]) => !init?.method || init.method === "POST")
      ).toBe(true);
      expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
      // A second click on the same entry must focus it again, without resetting the draft.
      screen.getByLabelText("Book title").focus();
      fireEvent.click(within(warning).getByRole("button", { name: /^View existing:/ }));
      await waitFor(() => expect(row).toHaveFocus());
    }
  );

  it("does not reset already enabled filters when viewing an active entry", async () => {
    setup(existing("watching", false));
    fireEvent.click(screen.getByRole("checkbox", { name: "Show archived" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Show released & owned" }));
    await importDraft();
    fireEvent.click(screen.getByRole("button", { name: /^View existing:/ }));
    await waitFor(() => expect(screen.getByRole("article")).toHaveFocus());
    expect(screen.getByRole("checkbox", { name: "Show archived" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Show released & owned" })).toBeChecked();
  });

  it("keeps the draft when a matching entry is no longer in the list", async () => {
    setup(existing("owned", true), { unavailable: true });
    await importDraft();
    fireEvent.click(screen.getByRole("button", { name: /^View existing:/ }));
    await screen.findByText(/Your draft is preserved/);
    expect(screen.getByLabelText("Book title")).toHaveValue("Imported title");
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("recovers from an archived-list load failure when View existing is retried", async () => {
    setup(existing("owned", true), { failArchiveLoad: true });
    await importDraft();
    fireEvent.click(screen.getByRole("button", { name: /^View existing:/ }));
    await screen.findByText(/Could not load the existing entry/);
    expect(screen.getByLabelText("Book title")).toHaveValue("Imported title");
    fireEvent.click(screen.getByRole("button", { name: /^View existing:/ }));
    const row = await screen.findByRole("article");
    await waitFor(() => expect(row).toHaveFocus());
  });

  it("updates medium comparisons and allows saving a different medium", async () => {
    setup(existing("owned", false));
    await importDraft();
    expect(screen.getByText("Same medium")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "Ebook" }));
    expect(screen.getByText("Choose a medium to compare")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "Audiobook" }));
    expect(screen.getByText("Different medium")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByLabelText("Book title")).not.toBeInTheDocument());
    const saved = fetchMock.mock.calls.find(
      ([url, init]) => url === "/api/releases/manual" && init?.method === "POST"
    );
    expect(saved).toBeDefined();
    expect(JSON.parse(String(saved?.[1]?.body))).toMatchObject({
      media: ["audiobook"],
      status: "watching",
    });
  });
});
