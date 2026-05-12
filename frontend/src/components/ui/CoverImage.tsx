import { useState } from "react";
import { BookOpen } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { LibraryBook } from "@/lib/api";

export function CoverImage({
  book,
  className = "aspect-[2/3] bg-surface-hover rounded-lg overflow-hidden flex items-center justify-center",
  fallbackIcon: Icon = BookOpen,
  iconClassName = "w-8 h-8 text-text-secondary opacity-40",
}: {
  book: LibraryBook;
  className?: string;
  fallbackIcon?: LucideIcon;
  iconClassName?: string;
}) {
  const [errored, setErrored] = useState(false);
  const src = !errored && book.cover_url ? book.cover_url : null;
  return (
    <div className={className}>
      {src ? (
        <img
          src={src}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
        />
      ) : (
        <Icon className={iconClassName} />
      )}
    </div>
  );
}
