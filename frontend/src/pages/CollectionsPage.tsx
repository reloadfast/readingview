import { useState } from "react";
import { ArrowLeft, BookOpen, FolderOpen, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { Button, CoverImage, Input, Skeleton } from "@/components/ui";
import {
  useAddToCollection,
  useCollectionDetail,
  useCollections,
  useCreateCollection,
  useDeleteCollection,
  useRemoveFromCollection,
  useUpdateCollection,
} from "@/hooks/useCollections";
import { useLibrary } from "@/hooks/useLibrary";
import type { CollectionOut, LibraryBook } from "@/lib/api";

// ---------------------------------------------------------------------------
// Skeletons
// ---------------------------------------------------------------------------

function CollectionCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-3 w-56" />
      <div className="flex items-center gap-3">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// New collection inline form
// ---------------------------------------------------------------------------

function NewCollectionForm({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const create = useCreateCollection();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), description: description.trim() || null },
      { onSuccess: onClose },
    );
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 rounded-xl bg-surface border border-border space-y-3"
    >
      <p className="text-sm font-semibold text-text-primary">New Collection</p>
      <Input
        required
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoFocus
      />
      <Input
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={create.isPending} pendingText="Creating…">
          Create
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Collection card (list view) — name, description, count, created date
// Pencil = inline rename; Trash = inline delete confirm
// ---------------------------------------------------------------------------

function CollectionCard({
  collection,
  onSelect,
}: {
  collection: CollectionOut;
  onSelect: () => void;
}) {
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState(collection.name);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const update = useUpdateCollection();
  const del = useDeleteCollection();

  const saveRename = () => {
    const trimmed = nameValue.trim();
    if (trimmed && trimmed !== collection.name) {
      update.mutate({ id: collection.id, body: { name: trimmed } });
    } else {
      setNameValue(collection.name);
    }
    setEditingName(false);
  };

  return (
    <div className="p-4 rounded-xl bg-surface border border-border space-y-2">
      <div className="flex items-start justify-between gap-2">
        {editingName ? (
          <Input
            className="text-sm font-semibold flex-1 h-7 py-0"
            value={nameValue}
            onChange={(e) => setNameValue(e.target.value)}
            onBlur={saveRename}
            onKeyDown={(e) => {
              if (e.key === "Enter") { e.preventDefault(); saveRename(); }
              if (e.key === "Escape") { setNameValue(collection.name); setEditingName(false); }
            }}
            autoFocus
          />
        ) : (
          <button
            className="text-sm font-semibold text-text-primary text-left flex-1 hover:text-accent transition-colors"
            onClick={onSelect}
          >
            {collection.name}
          </button>
        )}
        <div className="flex items-center gap-0.5 flex-shrink-0">
          <button
            onClick={() => { setEditingName(true); setNameValue(collection.name); }}
            className="p-1.5 rounded hover:bg-surface-hover text-text-secondary hover:text-text-primary"
            title="Rename"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setConfirmDelete(true)}
            className="p-1.5 rounded hover:bg-surface-hover text-text-secondary hover:text-accent-danger"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {collection.description && (
        <p className="text-xs text-text-secondary line-clamp-2">{collection.description}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-text-secondary">
        <span>{collection.book_count} book{collection.book_count !== 1 ? "s" : ""}</span>
        <span>{collection.created_at}</span>
      </div>

      {confirmDelete && (
        <div className="flex items-center gap-2 pt-1 border-t border-border mt-2">
          <span className="text-xs text-text-secondary">Delete?</span>
          <button
            className="text-xs text-red-500 hover:underline"
            onClick={() => del.mutate(collection.id)}
            disabled={del.isPending}
          >
            Yes
          </button>
          <button
            className="text-xs text-text-secondary hover:underline"
            onClick={() => setConfirmDelete(false)}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Add book panel — client-side library filter + checkbox multi-select
// ---------------------------------------------------------------------------

function AddBookPanel({
  collectionId,
  existingIds,
  onClose,
}: {
  collectionId: number;
  existingIds: Set<string>;
  onClose: () => void;
}) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { data: library, isLoading } = useLibrary({ limit: 10000 });
  const addMutation = useAddToCollection();

  const filtered = (library ?? []).filter(
    (b) =>
      !existingIds.has(b.id) &&
      (b.title.toLowerCase().includes(search.toLowerCase()) ||
        b.authors.toLowerCase().includes(search.toLowerCase())),
  );

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleAdd = async () => {
    for (const bookId of selected) {
      await addMutation.mutateAsync({ id: collectionId, absItemId: bookId });
    }
    onClose();
  };

  return (
    <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-text-primary">Add Books</p>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-surface-hover text-text-secondary hover:text-text-primary"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
        <Input
          className="pl-8"
          placeholder="Search by title or author…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
      </div>

      <div className="max-h-64 overflow-y-auto divide-y divide-border border border-border rounded-lg">
        {isLoading && (
          <div className="px-4 py-3 text-sm text-text-secondary">Loading library…</div>
        )}
        {!isLoading && filtered.length === 0 && (
          <div className="px-4 py-3 text-sm text-text-secondary">No books found</div>
        )}
        {filtered.map((book) => (
          <label
            key={book.id}
            className="flex items-center gap-3 px-4 py-2.5 hover:bg-surface-hover cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selected.has(book.id)}
              onChange={() => toggle(book.id)}
              className="accent-accent w-4 h-4 flex-shrink-0"
            />
            <CoverImage
              book={book}
              className="w-10 h-14 bg-surface-hover rounded flex items-center justify-center flex-shrink-0 overflow-hidden"
              iconClassName="w-4 h-4 text-text-secondary opacity-40"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary truncate">{book.title}</p>
              <p className="text-xs text-text-secondary truncate">{book.authors}</p>
            </div>
          </label>
        ))}
      </div>

      {selected.size > 0 && (
        <Button
          size="sm"
          onClick={handleAdd}
          disabled={addMutation.isPending}
          pendingText="Adding…"
        >
          Add {selected.size} book{selected.size !== 1 ? "s" : ""}
        </Button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Book row in detail view — cover art, title, author, remove confirm
// ---------------------------------------------------------------------------

function BookRow({
  book,
  collectionId,
}: {
  book: LibraryBook;
  collectionId: number;
}) {
  const [confirming, setConfirming] = useState(false);
  const remove = useRemoveFromCollection();

  return (
    <div className="flex items-center gap-3 py-2.5 px-1">
      <CoverImage book={book} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary truncate">{book.title}</p>
        <p className="text-xs text-text-secondary truncate">{book.authors}</p>
      </div>
      <div className="flex-shrink-0">
        {confirming ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary">Remove?</span>
            <button
              className="text-xs text-red-500 hover:underline"
              onClick={() => {
                remove.mutate({ id: collectionId, itemId: book.id });
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
            onClick={() => setConfirming(true)}
            className="p-1.5 rounded hover:bg-surface-hover text-text-secondary hover:text-accent-danger"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Collection detail view
// ---------------------------------------------------------------------------

function CollectionDetailView({
  collectionId,
  onBack,
}: {
  collectionId: number;
  onBack: () => void;
}) {
  const [showAddBook, setShowAddBook] = useState(false);
  const { data: detail, isLoading } = useCollectionDetail(collectionId);
  const { data: library } = useLibrary({ limit: 10000 });

  const bookMap = new Map((library ?? []).map((b) => [b.id, b]));
  const existingIds = new Set(detail?.item_ids ?? []);
  const books = (detail?.item_ids ?? [])
    .map((id) => bookMap.get(id))
    .filter((b): b is LibraryBook => b !== undefined);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          {isLoading ? (
            <Skeleton className="h-7 w-48" />
          ) : (
            <h1 className="text-2xl font-bold text-text-primary">{detail?.name}</h1>
          )}
        </div>
        <Button size="sm" variant="outline" onClick={() => setShowAddBook((v) => !v)}>
          <Plus className="w-4 h-4 mr-1" />
          Add Book
        </Button>
      </div>

      {detail?.description && (
        <p className="text-sm text-text-secondary">{detail.description}</p>
      )}

      {showAddBook && (
        <AddBookPanel
          collectionId={collectionId}
          existingIds={existingIds}
          onClose={() => setShowAddBook(false)}
        />
      )}

      {isLoading ? (
        <div className="divide-y divide-border">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 py-2.5 px-1">
              <Skeleton className="w-10 h-14 rounded flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
            </div>
          ))}
        </div>
      ) : books.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <BookOpen className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-sm text-text-secondary">No books in this collection yet.</p>
        </div>
      ) : (
        <div className="divide-y divide-border">
          {books.map((book) => (
            <BookRow key={book.id} book={book} collectionId={collectionId} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CollectionsPage() {
  const [showNewForm, setShowNewForm] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data, isLoading } = useCollections();

  if (selectedId !== null) {
    return (
      <CollectionDetailView
        collectionId={selectedId}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">Collections</h1>
        <Button
          size="sm"
          variant={showNewForm ? "outline" : "default"}
          onClick={() => setShowNewForm((v) => !v)}
        >
          <Plus className="w-4 h-4 mr-1" />
          New Collection
        </Button>
      </div>

      {showNewForm && (
        <NewCollectionForm onClose={() => setShowNewForm(false)} />
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <CollectionCardSkeleton key={i} />
          ))}
        </div>
      ) : (data ?? []).length === 0 && !showNewForm ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
          <FolderOpen className="w-12 h-12 text-text-secondary opacity-30" />
          <p className="text-lg font-medium text-text-primary">No collections yet.</p>
          <p className="text-sm text-text-secondary">
            Create one to organise your library.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(data ?? []).map((c) => (
            <CollectionCard
              key={c.id}
              collection={c}
              onSelect={() => setSelectedId(c.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
