/**
 * Display helpers for the earnings dashboard. Pure functions (unit-tested in frontend/tests/earnings).
 *
 * The API sends money as integer cents and dates as "YYYY-MM-DD" calendar dates. Calendar dates are
 * split into parts rather than parsed with `new Date("2026-07-01")`, which would mean UTC midnight.
 */

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

/** 2013500 -> "$20,135.00", -3500 -> "-$35.00" */
export function formatCents(cents: number): string {
  return money.format(cents / 100);
}

/** "2026-07-01" -> "Jul 1" (or "Jul 1, 2026" with the year) */
export function formatDate(isoDate: string, withYear = false): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const short = `${MONTH_NAMES[month - 1].slice(0, 3)} ${day}`;
  return withYear ? `${short}, ${year}` : short;
}

/** "2026-07" -> "July 2026" */
export function formatMonth(monthKey: string): string {
  const [year, month] = monthKey.split("-").map(Number);
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

/** "14:00:00" -> "2:00 PM" */
export function formatTime(clock: string): string {
  const [hours, minutes] = clock.split(":").map(Number);
  const suffix = hours < 12 ? "AM" : "PM";
  return `${((hours + 11) % 12) + 1}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

const CPT_LABELS: Record<string, string> = {
  "90791": "Intake (90791)",
  "90834": "Therapy 45 min (90834)",
  "90837": "Therapy 60 min (90837)",
};

export function serviceLabel(cpt: string): string {
  return CPT_LABELS[cpt] ?? cpt;
}
