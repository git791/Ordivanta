import React from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField?: keyof T;
  getRowKey?: (row: T, index: number) => string;
  emptyMessage?: string;
  className?: string;
}

export default function DataTable<T extends object>({
  columns, data, keyField, getRowKey, emptyMessage = 'No data', className,
}: DataTableProps<T>) {
  return (
    <div className={`overflow-x-auto ${className ?? ''}`}>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-surface-muted">
            {columns.map(col => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-3 text-left text-xs font-medium text-ink-muted uppercase tracking-wide border-b border-border ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-ink-muted">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, index) => {
              const rowObj = row as Record<string, unknown>;
              const rowKey = getRowKey
                ? getRowKey(row, index)
                : keyField
                ? String(row[keyField] ?? index)
                : String(index);
              return (
                <tr key={rowKey} className="border-b border-border hover:bg-surface-muted/50 transition-colors">
                  {columns.map(col => (
                    <td key={col.key} className={`px-4 py-3 text-ink ${col.className ?? ''}`}>
                      {col.render ? col.render(row) : String(rowObj[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
