import { describe, expect, it } from "vitest";
import type { MonthEarnings } from "@earnings/api";
import { barHeight, monthlyBars } from "@earnings/chart";
import { formatCents, formatDate, formatMonth } from "@earnings/format";

const m = (month: string, earned_cents: number, session_count = 1): MonthEarnings => ({
  month,
  earned_cents,
  session_count,
});

describe("earnings chart", () => {
  it("has twelve bars, January to December", () => {
    const bars = monthlyBars([m("2026-01", 100)], 2026);
    expect(bars.map((b) => b.label)).toEqual(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]);
    expect(bars.map((b) => b.month)).toEqual([
      "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
      "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12",
    ]);
  });

  it("keeps a month with no sessions in its own place", () => {
    // The API only lists months with sessions: here, nothing in August.
    const bars = monthlyBars([m("2026-07", 204800, 13), m("2026-09", 227800, 15), m("2026-10", 196200, 13)], 2026);
    const byLabel = Object.fromEntries(bars.map((b) => [b.label, b.earnedCents]));
    expect(byLabel).toMatchObject({ Jun: 0, Jul: 204800, Aug: 0, Sep: 227800, Oct: 196200, Nov: 0 });
    expect(bars.find((b) => b.month === "2026-09")?.sessionCount).toBe(15);
  });

  it("puts a provider who started mid-year on the right months", () => {
    const bars = monthlyBars([m("2026-05", 15800), m("2026-06", 31600, 2)], 2026);
    expect(bars.filter((b) => b.earnedCents > 0).map((b) => b.label)).toEqual(["May", "Jun"]);
    expect(bars[0].earnedCents).toBe(0);
  });

  it("shows an empty year as twelve zero bars", () => {
    const bars = monthlyBars([], 2027);
    expect(bars).toHaveLength(12);
    expect(bars.every((b) => b.earnedCents === 0 && b.sessionCount === 0)).toBe(true);
    expect(bars.map((b) => barHeight(b, bars))).toEqual(Array(12).fill(0));
  });

  it("sizes bars relative to the best month", () => {
    const bars = monthlyBars([m("2026-01", 50000), m("2026-02", 100000)], 2026);
    expect(barHeight(bars[0], bars)).toBe(50);
    expect(barHeight(bars[1], bars)).toBe(100);
  });
});

describe("earnings formatting", () => {
  it("formats cents, dates and months", () => {
    expect(formatCents(2013500)).toBe("$20,135.00");
    expect(formatDate("2026-07-01", true)).toBe("Jul 1, 2026");
    expect(formatMonth("2026-08")).toBe("August 2026");
  });
});
