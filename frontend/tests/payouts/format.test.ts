// Run as if in Dr. Patel's browser (Pacific time). Node applies a TZ change immediately, and the
// helpers only read the timezone when they're called.
process.env.TZ = "America/Los_Angeles";

import { describe, expect, it } from "vitest";
import { formatCents, formatDate, formatPeriod, formatTime } from "@payouts/format";

describe("provider portal formatting", () => {
  it("shows a date of service as that calendar day", () => {
    expect(formatDate("2026-10-15")).toBe("Oct 15");
    expect(formatDate("2026-10-01", true)).toBe("Oct 1, 2026");
  });

  it("labels a pay period with its own first and last day", () => {
    expect(formatPeriod("2026-10-01", "2026-10-15")).toBe("Oct 1 – Oct 15, 2026");
    expect(formatPeriod("2026-12-16", "2026-12-31")).toBe("Dec 16 – Dec 31, 2026");
  });

  it("labels a January period with the new year", () => {
    expect(formatPeriod("2027-01-01", "2027-01-15")).toBe("Jan 1 – Jan 15, 2027");
  });

  it("doesn't roll New Year's Day back into the previous year", () => {
    // Parsed as UTC midnight, "2027-01-01" would be Dec 31, 2026 in Pacific time.
    expect(formatDate("2027-01-01", true)).toBe("Jan 1, 2027");
    expect(formatDate("2026-12-31", true)).toBe("Dec 31, 2026");
    expect(formatPeriod("2026-12-16", "2026-12-31")).toBe("Dec 16 – Dec 31, 2026");
  });

  it("shows session times on the provider's clock", () => {
    expect(formatTime("2026-10-16T01:30:00Z", "America/Los_Angeles")).toBe("6:30 PM PDT");
    expect(formatTime("2026-10-16T01:00:00Z", "America/New_York")).toBe("9:00 PM EDT");
  });

  it("formats cents as dollars", () => {
    expect(formatCents(127050)).toBe("$1,270.50");
    expect(formatCents(-3500)).toBe("-$35.00");
  });
});
