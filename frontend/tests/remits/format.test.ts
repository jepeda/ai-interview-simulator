// Run as if in a billing specialist's browser (Eastern time).
process.env.TZ = "America/New_York";

import { describe, expect, it } from "vitest";
import { formatAccounting, formatDate, formatReceived } from "@remits/format";

describe("claims portal formatting", () => {
  it("formats positive amounts as dollars", () => {
    expect(formatAccounting(0)).toBe("$0.00");
    expect(formatAccounting(1)).toBe("$0.01");
    expect(formatAccounting(13717)).toBe("$137.17");
    expect(formatAccounting(123456)).toBe("$1,234.56");
  });

  it("shows negative amounts in parentheses, like the EOB", () => {
    expect(formatAccounting(-3500)).toBe("($35.00)");
    expect(formatAccounting(-4215)).toBe("($42.15)");
    expect(formatAccounting(-19998)).toBe("($199.98)");
  });

  it("keeps the dollars of a negative amount under $1 and above $1,000", () => {
    expect(formatAccounting(-1)).toBe("($0.01)");
    expect(formatAccounting(-50)).toBe("($0.50)");
    expect(formatAccounting(-123456)).toBe("($1,234.56)");
  });

  it("shows calendar dates as that day", () => {
    expect(formatDate("2026-10-09")).toBe("Oct 9, 2026");
    expect(formatDate("2027-01-01")).toBe("Jan 1, 2027");
  });

  it("shows when a file arrived on Eastern time", () => {
    expect(formatReceived("2026-10-12T13:47:00Z")).toBe("Oct 12, 9:47 AM");
  });
});
