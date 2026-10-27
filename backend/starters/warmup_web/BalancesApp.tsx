import { useEffect, useState } from "react";
import { getBalances, type BalancesReport } from "./api";
import { sortLargestFirst } from "./balances";
import { formatCents, formatDate } from "./format";

export function BalancesApp() {
  const [report, setReport] = useState<BalancesReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBalances(1)
      .then(setReport)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="card error">{error}</div>;
  if (!report) return <div className="card">Loading…</div>;
  return (
    <div className="page">
      <header>
        <strong>Billing</strong> · {report.provider.name}
      </header>
      <section className="card">
        <div className="total">
          <span>Outstanding client balances</span>
          <strong>{formatCents(report.total_cents)}</strong>
        </div>
        <p className="hint">Largest balances first, so the front desk knows who to follow up with.</p>
        <table>
          <thead>
            <tr>
              <th>Client</th>
              <th>Date of service</th>
              <th className="num">Owes</th>
              <th className="num">Paid</th>
              <th className="num">Balance</th>
            </tr>
          </thead>
          <tbody>
            {sortLargestFirst(report.lines).map((line) => (
              <tr key={line.invoice_id}>
                <td>{line.client_name}</td>
                <td>{formatDate(line.service_date)}</td>
                <td className="num">{formatCents(line.responsibility_cents)}</td>
                <td className="num">{formatCents(line.paid_cents)}</td>
                <td className="num">
                  <strong>{formatCents(line.balance_cents)}</strong>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
