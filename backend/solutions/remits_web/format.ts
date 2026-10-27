/**
 * Display helpers for the claims portal. Pure functions (unit-tested in frontend/tests/remits).
 *
 * The API sends money as integer cents, calendar dates as "YYYY-MM-DD" and instants as ISO-8601
 * UTC strings. Billing ops reads money the way EOBs print it: negatives in parentheses.
 */

const accounting = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  currencySign: "accounting",
});

/**
 * Accounting style: 123456 -> "$1,234.56", -4215 -> "($42.15)"
 *
 * Intl does the sign and rounding; dividing cents by 100 is fine for display only.
 * (Hand-rolled Math.floor(cents / 100) was wrong for negatives: floor(-42.15) is -43.)
 */
export function formatAccounting(cents: number): string {
  return accounting.format(cents / 100);
}

/** "2026-10-09" -> "Oct 9, 2026" (a calendar date: no timezone conversion) */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** When a file arrived, on Acme Health's (Eastern) clock: "2026-10-12T13:47:00Z" -> "Oct 12, 9:47 AM" */
export function formatReceived(isoInstant: string): string {
  return new Date(isoInstant).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  paid: "Paid",
  partially_paid: "Partially paid",
  overpaid: "Overpaid",
  denied: "Denied",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

const CPT_LABELS: Record<string, string> = {
  "90791": "Intake (90791)",
  "90834": "Therapy 45 min (90834)",
  "90837": "Therapy 60 min (90837)",
};

export function serviceLabel(cpt: string): string {
  return CPT_LABELS[cpt] ?? cpt;
}
