import type { BalanceLine } from "./api";

/** The collections view: who owes the most comes first (ties: oldest date of service first). */
export function sortLargestFirst(lines: BalanceLine[]): BalanceLine[] {
  return [...lines].sort((a, b) => b.balance_cents - a.balance_cents || a.service_date.localeCompare(b.service_date));
}
