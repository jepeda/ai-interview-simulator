import type { BalanceLine } from "./api";
import { formatCents } from "./format";

/** The collections view: who owes the most comes first. */
export function sortLargestFirst(lines: BalanceLine[]): BalanceLine[] {
  return [...lines].sort((a, b) => formatCents(b.balance_cents).localeCompare(formatCents(a.balance_cents)));
}
