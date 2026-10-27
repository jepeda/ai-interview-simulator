import { useEffect, useState } from "react";
import { getWeek, type WeekCard } from "./api";
import { formatCents, formatDay } from "./format";

const STATUS_LABEL: Record<string, string> = {
  completed: "Session",
  late_cancel: "Late cancel",
  no_show: "No-show",
};

export function WeekApp() {
  const [card, setCard] = useState<WeekCard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWeek(1, "2026-10-19")
      .then(setCard)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="card error">{error}</div>;
  if (!card) return <div className="card">Loading…</div>;
  return (
    <div className="page">
      <header>
        <strong>Earnings</strong> · {card.provider.name}
      </header>
      <section className="card">
        <div className="total">
          <span>
            This week · {formatDay(card.week_start)} – {formatDay(card.week_end)}
          </span>
          <strong>{formatCents(card.total_cents)}</strong>
        </div>
        <table>
          <thead>
            <tr>
              <th>Day</th>
              <th>Client</th>
              <th>Service</th>
              <th>Payer</th>
              <th>Type</th>
              <th className="num">Amount</th>
            </tr>
          </thead>
          <tbody>
            {card.lines.map((line) => (
              <tr key={line.session_id}>
                <td>{formatDay(line.date)}</td>
                <td>{line.client_name}</td>
                <td>{line.cpt_code}</td>
                <td>{line.payer}</td>
                <td>{STATUS_LABEL[line.status] ?? line.status}</td>
                <td className="num">{formatCents(line.amount_cents)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
