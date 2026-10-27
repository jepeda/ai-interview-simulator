import type { Appointments, Eligibility, Patient, PatientPage, Plan } from "./types";

const BASE = "/clinic-api";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`HTTP ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json" },
  });
  const text = await res.text();
  let body: unknown = text;
  try {
    body = JSON.parse(text);
  } catch {
    /* plain-text error (e.g. a 500 from uvicorn) */
  }
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

export const clinicApi = {
  listPatients: (params: { includeArchived: boolean; payer: string }) => {
    const q = new URLSearchParams({ page_size: "100" });
    if (params.includeArchived) q.set("include_archived", "true");
    if (params.payer) q.set("payer", params.payer);
    return request<PatientPage>(`/patients?${q}`);
  },
  plans: () => request<Plan[]>("/plans"),
  patient: (id: number) => request<Patient>(`/patients/${id}`),
  eligibility: (id: number, on: string) => request<Eligibility>(`/patients/${id}/eligibility?on=${on}`),
  appointments: (id: number) => request<Appointments>(`/patients/${id}/appointments`),
  updateCoverage: (id: number, body: { insurance_plan_id: number | null; member_id: string | null }) =>
    request<Patient>(`/patients/${id}/coverage`, { method: "PATCH", body: JSON.stringify(body) }),
  createPatient: (body: Record<string, unknown>) =>
    request<Patient>("/patients", { method: "POST", body: JSON.stringify(body) }),
};

/** Turn a FastAPI 422 body (or anything else) into readable lines. */
export function describeError(err: unknown): string[] {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: unknown };
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).slice(1).join(".") || "body"}: ${d.msg}`);
    }
    if (body && typeof body === "object" && "detail" in body) return [`${err.status}: ${String(body.detail)}`];
    return [`${err.status}: ${String(err.body).slice(0, 300) || "Internal Server Error (see the clinic terminal for the traceback)"}`];
  }
  return [String(err)];
}
