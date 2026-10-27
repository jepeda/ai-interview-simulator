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
  suspense_cents: number;
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

export interface SuspenseLine {
  id: number;
  remittance_id: number;
  payer: string;
  trace_number: string;
  paid_on: string;
  claim_number: string; // as the payer sent it
  billed_cents: number;
  paid_cents: number;
}

export interface RemittanceDetail extends RemittanceSummary {
  lines: RemitLine[];
  remit_adjustments: RemitAdjustment[];
  unmatched_lines: SuspenseLine[];
}

export type AgingBucket = "0-30" | "31-60" | "61-90" | "90+";

export interface Denial {
  claim_number: string;
  patient_name: string;
  provider_name: string;
  payer: string;
  cpt_code: string;
  date_of_service: string;
  billed_cents: number;
  denial_code: string;
  denial_reason: string;
  denied_on: string;
  days_outstanding: number;
  bucket: AgingBucket;
}

export interface DenialQueue {
  as_of: string;
  buckets: Record<AgingBucket, number>;
  claims: Denial[];
}

export interface Underpayment {
  claim_number: string;
  patient_name: string;
  payer: string;
  cpt_code: string;
  date_of_service: string;
  expected_cents: number;
  allowed_cents: number;
  variance_cents: number;
}

export interface UnderpaymentReport {
  tolerance_cents: number;
  total_variance_cents: number;
  claims: Underpayment[];
}

export const API_BASE = "/remits-api";

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
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
  denials: (filters: { payer?: string; code?: string } = {}) => get<DenialQueue>(`/denials${query(filters)}`),
  underpayments: () => get<UnderpaymentReport>("/underpayments"),
  suspense: () => get<SuspenseLine[]>("/suspense"),
  matchSuspense: (id: number, claimNumber: string) =>
    get<ClaimDetail>(`/suspense/${id}/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim_number: claimNumber }),
    }),
};
