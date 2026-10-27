import { useEffect, useState } from "react";
import { payoutsApi, type PeriodSummary, type Provider, type Statement } from "./api";
import { formatCents, formatDate, formatPeriod, formatTime, serviceLabel } from "./format";

const KIND_LABELS: Record<string, string> = { session: "Session", late_cancel: "Late cancel" };

/** Acme Health's provider portal: pick a provider, see their pay periods and statements. */
export function PortalApp() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerId, setProviderId] = useState<number | null>(null);
  const [periods, setPeriods] = useState<PeriodSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [statement, setStatement] = useState<Statement | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    payoutsApi
      .providers()
      .then((list) => {
        setProviders(list);
        setProviderId((current) => current ?? list[0]?.id ?? null);
      })
      .catch((e: Error) => setError(`Can't reach the payouts API (port 8713): ${e.message}`));
  }, []);

  useEffect(() => {
    if (providerId === null) return;
    setStatement(null);
    payoutsApi
      .periods(providerId)
      .then((list) => {
        setPeriods(list);
        setSelected(list[0]?.period_start ?? null);
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, [providerId]);

  useEffect(() => {
    if (providerId === null || selected === null) return;
    payoutsApi
      .statement(providerId, selected)
      .then(setStatement)
      .catch((e: Error) => setError(e.message));
  }, [providerId, selected]);

  return (
    <div className="portal">
      <header className="portal-header">
        <div className="portal-brand">
          <span className="portal-logo">A</span> Provider portal
        </div>
        <label className="portal-provider">
          Signed in as
          <select value={providerId ?? ""} onChange={(e) => setProviderId(Number(e.target.value))}>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
      </header>

      {error && <div className="portal-error">{error}</div>}

      <main className="portal-main">
        <section className="portal-card periods">
          <h2>Payments</h2>
          <ul>
            {periods.map((p) => (
              <li key={p.period_start}>
                <button
                  className={p.period_start === selected ? "active" : ""}
                  onClick={() => setSelected(p.period_start)}
                >
                  <span>{formatPeriod(p.period_start, p.period_end)}</span>
                  <span className="muted">
                    {p.session_count} session{p.session_count === 1 ? "" : "s"}
                  </span>
                  <strong className={p.total_cents < 0 ? "negative" : ""}>{formatCents(p.total_cents)}</strong>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="portal-card statement">
          {statement ? (
            <>
              <div className="statement-head">
                <div>
                  <h2>Statement · {formatPeriod(statement.period_start, statement.period_end)}</h2>
                  <p className="muted">
                    {statement.provider.name} · NPI {statement.provider.npi} · times in {statement.provider.timezone}
                  </p>
                </div>
                <div className="statement-total">
                  <span className="muted">Total</span>
                  <strong className={statement.total_cents < 0 ? "negative" : ""}>
                    {formatCents(statement.total_cents)}
                  </strong>
                  {statement.payout_cents !== statement.total_cents && (
                    <span className="muted">Payout: {formatCents(statement.payout_cents)} (balance carries over)</span>
                  )}
                  <span className="muted">
                    Pay date: {statement.pay_date ? formatDate(statement.pay_date, true) : "pending"}
                  </span>
                  <a href={payoutsApi.statementCsvUrl(statement.provider.id, statement.period_start)} download>
                    Download CSV
                  </a>
                </div>
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Client</th>
                    <th>Service</th>
                    <th>Payer</th>
                    <th>Type</th>
                    <th className="num">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {statement.lines.map((line) => (
                    <tr key={line.appointment_id}>
                      <td>{formatDate(line.service_date)}</td>
                      <td className="muted">{formatTime(line.starts_at, statement.provider.timezone)}</td>
                      <td>{line.client_name}</td>
                      <td>{serviceLabel(line.cpt_code)}</td>
                      <td>{line.payer}</td>
                      <td>{KIND_LABELS[line.kind] ?? line.kind}</td>
                      <td className="num">{formatCents(line.amount_cents)}</td>
                    </tr>
                  ))}
                  {statement.lines.length === 0 && (
                    <tr>
                      <td colSpan={7} className="muted">
                        No billable sessions in this period.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {statement.adjustments.length > 0 && (
                <>
                  <h3>Adjustments</h3>
                  <table>
                    <tbody>
                      {statement.adjustments.map((a, i) => (
                        <tr key={a.id ?? `carry-${i}`}>
                          <td>{formatDate(a.effective_date)}</td>
                          <td>{a.reason}</td>
                          <td className={`num ${a.amount_cents < 0 ? "negative" : ""}`}>{formatCents(a.amount_cents)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </>
          ) : (
            <p className="muted">{periods.length ? "Loading statement…" : "No pay periods yet."}</p>
          )}
        </section>
      </main>
    </div>
  );
}
