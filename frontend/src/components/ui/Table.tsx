import { cn } from "@/lib/utils";

export interface Column<T> {
  key: keyof T | string;
  header: string;
  className?: string;
  cell?: (row: T) => React.ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  className?: string;
  rowKey: (row: T) => string | number;
}

export function Table<T>({ columns, data, className, rowKey }: TableProps<T>) {
  return (
    <div className={cn("w-full overflow-auto", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={cn(
                  "py-3 px-4 text-left text-text-secondary font-medium",
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={rowKey(row)}
              className="border-b border-border hover:bg-surface-hover transition-colors"
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={cn("py-3 px-4 text-text-primary", col.className)}
                >
                  {col.cell
                    ? col.cell(row)
                    : String(
                        (row as Record<string, unknown>)[String(col.key)] ?? ""
                      )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
