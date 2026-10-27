/** Display helpers for the earnings card. */

/** 76000 -> "$760.00", 123456 -> "$1,234.56" */
export function formatCents(cents: number): string {
  return `$${cents / 100}`;
}

/** "2026-10-19" -> "Mon Oct 19" */
export function formatDay(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}
