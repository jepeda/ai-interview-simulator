/**
 * Data for the "Earnings by month" chart. Pure functions (unit-tested in frontend/tests/earnings).
 */

import type { MonthEarnings } from "./api";

export const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export interface MonthBar {
  month: string; // "2026-07", the key the month-detail endpoint takes
  label: string; // "Jul"
  earnedCents: number;
  sessionCount: number;
}

/** (2026, 7) -> "2026-07" */
export function monthKey(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}`;
}

/** The chart's twelve bars, January to December of `year`, from the API's monthly totals. */
export function monthlyBars(months: MonthEarnings[], year: number): MonthBar[] {
  return MONTH_LABELS.map((label, i) => ({
    month: monthKey(year, i + 1),
    label,
    earnedCents: months[i]?.earned_cents ?? 0,
    sessionCount: months[i]?.session_count ?? 0,
  }));
}

/** Bar height as a percentage of the tallest bar (0 for every bar when there's nothing yet). */
export function barHeight(bar: MonthBar, bars: MonthBar[]): number {
  const tallest = Math.max(0, ...bars.map((b) => b.earnedCents));
  return tallest > 0 ? Math.round((bar.earnedCents / tallest) * 100) : 0;
}
