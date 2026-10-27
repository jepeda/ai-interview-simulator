/**
 * Display helpers for the provider portal. Pure functions (unit-tested in frontend/tests/payouts).
 *
 * The API sends money as integer cents, dates of service / pay periods as "YYYY-MM-DD" calendar
 * dates (already on the provider's calendar), and instants as ISO-8601 UTC strings.
 */

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** 132050 -> "$1,320.50", -3500 -> "-$35.00" */
export function formatCents(cents: number): string {
  return money.format(cents / 100);
}

/** "2026-10-15" -> "Oct 15" (or "Oct 15, 2026" with the year) */
export function formatDate(isoDate: string, withYear = false): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    ...(withYear ? { year: "numeric" } : {}),
  });
}

/** ("2026-10-01", "2026-10-15") -> "Oct 1 – Oct 15, 2026" */
export function formatPeriod(startIso: string, endIso: string): string {
  const year = new Date(endIso).getFullYear();
  return `${formatDate(startIso)} – ${formatDate(endIso)}, ${year}`;
}

/** An instant shown on the provider's clock: ("2026-10-16T01:30:00Z", "America/Los_Angeles") -> "6:30 PM PDT" */
export function formatTime(isoInstant: string, timeZone: string): string {
  return new Date(isoInstant).toLocaleTimeString("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

const CPT_LABELS: Record<string, string> = {
  "90791": "Intake (90791)",
  "90834": "Therapy 45 min (90834)",
  "90837": "Therapy 60 min (90837)",
};

export function serviceLabel(cpt: string): string {
  return CPT_LABELS[cpt] ?? cpt;
}
