import { describe, expect, it } from "vitest";
import { formatCents } from "@sandbox/format";

describe("earnings card formatting", () => {
  it("always shows cents", () => {
    expect(formatCents(76000)).toBe("$760.00");
    expect(formatCents(7500)).toBe("$75.00");
  });

  it("groups thousands", () => {
    expect(formatCents(123456)).toBe("$1,234.56");
  });
});
