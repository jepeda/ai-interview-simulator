/** Typed client for the payouts API (proxied by Vite: /payouts-api/* -> http://127.0.0.1:8713/*). */

export interface Provider {
  id: number;
  name: string;
  npi: string;
  timezone: string;
}

export interface StatementLine {
  appointment_id: number;
  service_date: string; // YYYY-MM-DD
  starts_at: string; // ISO UTC
  client_name: string;
  cpt_code: string;
  payer: string;
  status: string;
  kind: "session" | "late_cancel";
  amount_cents: number;
}

export interface AdjustmentLine {
  id: number | null;
  effective_date: string; // YYYY-MM-DD
  reason: string;
  amount_cents: number;
}

export interface Statement {
  provider: Provider;
  period_start: string;
  period_end: string;
  lines: StatementLine[];
  adjustments: AdjustmentLine[];
  total_cents: number;
  payout_cents: number;
  pay_date: string | null;
}

export interface PeriodSummary {
  period_start: string;
  period_end: string;
  session_count: number;
  total_cents: number;
  payout_cents: number;
  pay_date: string | null;
}

export const API_BASE = "/payouts-api";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const payoutsApi = {
  providers: () => get<Provider[]>("/providers"),
  periods: (providerId: number) => get<PeriodSummary[]>(`/providers/${providerId}/periods`),
  statement: (providerId: number, periodStart: string) =>
    get<Statement>(`/providers/${providerId}/statements/${periodStart}`),
  statementCsvUrl: (providerId: number, periodStart: string) =>
    `${API_BASE}/providers/${providerId}/statements/${periodStart}.csv`,
};
