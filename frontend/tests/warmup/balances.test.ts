import { describe, expect, it } from "vitest";
import type { BalanceLine } from "@warmup/api";
import { sortLargestFirst } from "@warmup/balances";

const line = (invoice_id: number, balance_cents: number, service_date = "2026-10-01"): BalanceLine => ({
  invoice_id,
  client_name: `Client ${invoice_id}`,
  service_date,
  responsibility_cents: balance_cents,
  paid_cents: 0,
  balance_cents,
});

describe("collections view", () => {
  it("puts the largest balance first", () => {
    const sorted = sortLargestFirst([line(1, 2667), line(2, 15335), line(3, 9167), line(4, 3000)]);
    expect(sorted.map((l) => l.balance_cents)).toEqual([15335, 9167, 3000, 2667]);
  });

  it("orders four-digit dollar amounts correctly", () => {
    const sorted = sortLargestFirst([line(1, 99900), line(2, 120000), line(3, 5000)]);
    expect(sorted.map((l) => l.invoice_id)).toEqual([2, 1, 3]);
  });

  it("breaks ties by the oldest date of service", () => {
    const sorted = sortLargestFirst([line(1, 5000, "2026-10-09"), line(2, 5000, "2026-09-01")]);
    expect(sorted.map((l) => l.invoice_id)).toEqual([2, 1]);
  });

  it("doesn't change the list it was given", () => {
    const lines = [line(1, 100), line(2, 200)];
    sortLargestFirst(lines);
    expect(lines.map((l) => l.invoice_id)).toEqual([1, 2]);
  });
});
