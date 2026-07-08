import type { HazopRow } from "./data";

// Group worksheet rows by their cause, preserving first-appearance order, so the
// grid can render the Cause -> Consequence hierarchy: each cause appears once
// with its consequence rows beneath it, instead of being repeated.
export function groupRowsByCause(rows: HazopRow[]): { key: string; rows: HazopRow[] }[] {
  const groups: { key: string; rows: HazopRow[] }[] = [];
  const indexByKey = new Map<string, number>();

  for (const row of rows) {
    const key = row.cause.trim() ? `cause:${row.cause.trim()}` : `row:${row.id}`;
    const existing = indexByKey.get(key);

    if (existing === undefined) {
      indexByKey.set(key, groups.length);
      groups.push({ key, rows: [row] });
    } else {
      groups[existing].rows.push(row);
    }
  }

  return groups;
}
