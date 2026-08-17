import type { ReactNode } from "react";
import { useSettings } from "@/hooks/useSettings";

function absItemUrl(baseUrl: string, itemId: string) {
  return `${baseUrl.replace(/\/+$/, "")}/item/${encodeURIComponent(itemId)}`;
}

export function AbsBookLink({
  itemId,
  children,
  className,
}: {
  itemId: string;
  children: ReactNode;
  className?: string;
}) {
  const { data: settings } = useSettings();
  const href = settings?.abs_url ? absItemUrl(settings.abs_url, itemId) : null;

  return (
    <a
      href={href ?? undefined}
      target={href ? "_blank" : undefined}
      rel={href ? "noreferrer" : undefined}
      className={className}
      title={href ? "Open in Audiobookshelf" : undefined}
    >
      {children}
    </a>
  );
}
