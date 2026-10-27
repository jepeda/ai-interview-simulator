/** Typed client for the remits API (proxied by Vite: /remits-api/* -> http://127.0.0.1:8714/*). */

export type ClaimStatus = "submitted" | "paid" | "partially_paid" | "overpaid" | "denied";

export interface Adjustment {
  group_code: string; // CO, PR, OA, PI
  reason_code: string; // CARC: 45, 1, 2, 3, 197...
  code: string; // "CO-45"
  description: string;
  amount_cents: number;
}

export interface ClaimSummary {
  claim_number: string;
  provider_name: string;
  patient_name: string;
  payer: string;
  cpt_code: string;
  date_of_service: string; // YYYY-MM-DD
  billed_cents: number;
  paid_cents: number;
  adjusted_cents: number;
  patient_resp_cents: number;
  balance_cents: number;
  status: ClaimStatus;
}

export interface ClaimPayment {
  remittance_id: number;
  trace_number: string;
  paid_on: string; // YYYY-MM-DD
  status_code: string;
  status_description: string;
  billed_cents: number;
  paid_cents: number;
  adjustments: Adjustment[];
}

export interface ClaimDetail extends ClaimSummary {
  contracted_allowed_cents: number | null;
  payments: ClaimPayment[];
}

export interface RemittanceSummary {
  id: number;
  payer: string;
  trace_number: string;
  payment_method: "ACH" | "CHK";
  paid_on: string; // YYYY-MM-DD
  received_at: string; // ISO UTC
  total_paid_cents: number;
  posted_cents: number;
  out_of_balance_cents: number;
  claim_count: number;
}

export interface RemitLine {
  claim_number: string;
  patient_name: string;
  status_code: string;
  billed_cents: number;
  paid_cents: number;
  adjustments: Adjustment[];
}

export interface RemitAdjustment {
  code: string;
  description: string;
  reference: string;
  amount_cents: number;
}

export interface RemittanceDetail extends RemittanceSummary {
  lines: RemitLine[];
  remit_adjustments: RemitAdjustment[];
}

export const API_BASE = "/remits-api";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

function query(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter((entry): entry is [string, string] => Boolean(entry[1]));
  return entries.length ? `?${new URLSearchParams(entries)}` : "";
}

export const remitsApi = {
  claims: (filters: { status?: ClaimStatus; payer?: string; q?: string } = {}) =>
    get<ClaimSummary[]>(`/claims${query(filters)}`),
  claim: (claimNumber: string) => get<ClaimDetail>(`/claims/${encodeURIComponent(claimNumber)}`),
  remittances: () => get<RemittanceSummary[]>("/remittances"),
  remittance: (id: number) => get<RemittanceDetail>(`/remittances/${id}`),
};
