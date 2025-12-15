import { ReactNode } from "react";
import { Button } from "../ui/button";
import { cn } from "../../utils/cn";

export type Column<T> = {
  key: keyof T | string;
  header: string;
  render?: (row: T) => ReactNode;
};

type Props<T> = {
  data: T[];
  columns: Column<T>[];
  onEdit?: (row: T) => void;
  onDelete?: (row: T) => void;
  loading?: boolean;
};

export function DataTable<T extends { id: number | string }>({ data, columns, onEdit, onDelete, loading }: Props<T>) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-white">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
          <tr>
            {columns.map((col) => (
              <th key={String(col.key)} className="px-3 py-2 font-semibold">
                {col.header}
              </th>
            ))}
            {(onEdit || onDelete) && <th className="px-3 py-2 text-right">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td className="px-3 py-4 text-center text-gray-500" colSpan={columns.length + 1}>
                Loading...
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td className="px-3 py-4 text-center text-gray-500" colSpan={columns.length + 1}>
                No records
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr key={row.id} className={cn("border-t border-border hover:bg-gray-50")}>
                {columns.map((col) => (
                  <td key={String(col.key)} className="px-3 py-2">
                    {col.render ? col.render(row) : String((row as any)[col.key])}
                  </td>
                ))}
                {(onEdit || onDelete) && (
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      {onEdit && (
                        <Button variant="ghost" size="sm" onClick={() => onEdit(row)}>
                          Edit
                        </Button>
                      )}
                      {onDelete && (
                        <Button variant="destructive" size="sm" onClick={() => onDelete(row)}>
                          Delete
                        </Button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
