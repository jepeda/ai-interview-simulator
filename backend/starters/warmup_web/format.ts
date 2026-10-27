/** Display helpers. */

const dollars = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** 32669 -> "$326.69" */
export function formatCents(cents: number): string {
  return dollars.format(cents / 100);
}

/** "2026-10-01" -> "Oct 1, 2026" */
export function formatDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}
