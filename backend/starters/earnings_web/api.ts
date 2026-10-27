/** Typed client for the earnings API (proxied by Vite: /earnings-api/* -> http://127.0.0.1:8715/*). */

export interface Provider {
  id: number;
  name: string;
  npi: string;
  license: string;
  state: string;
}

export interface MonthEarnings {
  month: string; // "2026-07"
  session_count: number;
  earned_cents: number;
}

export interface PayerEarnings {
  payer: string;
  session_count: number;
  earned_cents: number;
}

export interface EarningsSummary {
  provider: Provider;
  year: number;
  session_count: number;
  total_cents: number;
  months: MonthEarnings[];
  by_payer: PayerEarnings[];
}

export interface EarningLine {
  appointment_id: number;
  service_date: string; // YYYY-MM-DD
  start_time: string; // "14:00:00", provider-local
  client_name: string;
  cpt_code: string;
  payer: string;
  rate_cents: number;
  paid_on: string | null; // YYYY-MM-DD
}

export interface MonthDetail {
  provider_id: number;
  month: string;
  session_count: number;
  total_cents: number;
  lines: EarningLine[];
}

export interface RateChange {
  rate_cents: number;
  effective_date: string; // YYYY-MM-DD
}

export interface RateCardRow {
  payer: string;
  cpt_code: string;
  current: RateChange | null;
  upcoming: RateChange | null;
}

export const API_BASE = "/earnings-api";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const earningsApi = {
  providers: () => get<Provider[]>("/providers"),
  summary: (providerId: number, year: number) =>
    get<EarningsSummary>(`/providers/${providerId}/earnings?year=${year}`),
  month: (providerId: number, month: string) => get<MonthDetail>(`/providers/${providerId}/earnings/${month}`),
  rateCard: (providerId: number) => get<RateCardRow[]>(`/providers/${providerId}/rate-card`),
};
