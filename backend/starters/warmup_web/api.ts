/** Typed client for the warmup API (proxied by Vite: /warmup-api/* -> http://127.0.0.1:8717/*). */

export interface BalanceLine {
  invoice_id: number;
  client_name: string;
  service_date: string; // YYYY-MM-DD
  responsibility_cents: number;
  paid_cents: number;
  balance_cents: number;
}

export interface BalancesReport {
  provider: { id: number; name: string };
  lines: BalanceLine[];
  total_cents: number;
}

export async function getBalances(providerId: number): Promise<BalancesReport> {
  const res = await fetch(`/warmup-api/providers/${providerId}/balances`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return (await res.json()) as BalancesReport;
}
