/** Typed client for the sandbox API (proxied by Vite: /sandbox-api/* -> http://127.0.0.1:8716/*). */

export interface WeekLine {
  session_id: number;
  date: string; // YYYY-MM-DD
  client_name: string;
  cpt_code: string;
  payer: string;
  status: string;
  amount_cents: number;
}

export interface WeekCard {
  provider: { id: number; name: string };
  week_start: string;
  week_end: string;
  lines: WeekLine[];
  total_cents: number;
}

export async function getWeek(providerId: number, start: string, payer?: string): Promise<WeekCard> {
  const params = new URLSearchParams({ start });
  if (payer) params.set("payer", payer);
  const res = await fetch(`/sandbox-api/providers/${providerId}/week?${params}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return (await res.json()) as WeekCard;
}
