import { describe, expect, it } from "vitest";
import { clock, sessionElapsed } from "../../src/components/interviewClock";

describe("clock", () => {
  it("formats seconds as m:ss", () => {
    expect(clock(0)).toBe("0:00");
    expect(clock(65)).toBe("1:05");
    expect(clock(3600)).toBe("60:00");
  });

  it("shows overtime with a minus sign", () => {
    expect(clock(-90)).toBe("-1:30");
  });
});

describe("sessionElapsed", () => {
  const start = Date.UTC(2026, 9, 26, 15, 0, 0);
  const iso = (ms: number) => new Date(ms).toISOString();

  it("counts whole seconds since the start", () => {
    expect(sessionElapsed({ started_at: iso(start) }, start + 61_500)).toBe(61);
  });

  it("subtracts finished pauses", () => {
    expect(sessionElapsed({ started_at: iso(start), paused_seconds: 600 }, start + 900_000)).toBe(300);
  });

  it("freezes while paused", () => {
    const session = { started_at: iso(start), paused_seconds: 0, paused_at: iso(start + 100_000) };
    expect(sessionElapsed(session, start + 100_000)).toBe(100);
    expect(sessionElapsed(session, start + 700_000)).toBe(100);
  });

  it("never goes negative", () => {
    expect(sessionElapsed({ started_at: iso(start) }, start - 5_000)).toBe(0);
  });
});
