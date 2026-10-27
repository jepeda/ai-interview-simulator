import { useEffect, useMemo, useState } from "react";
import { earningsApi, type EarningsSummary, type MonthDetail, type Provider, type RateCardRow } from "./api";
import { barHeight, monthlyBars } from "./chart";
import { formatCents, formatDate, formatMonth, formatTime, serviceLabel } from "./format";

const THIS_YEAR = new Date().getFullYear();
const YEARS = [THIS_YEAR, THIS_YEAR - 1];

/** Acme Health's earnings dashboard: pick a provider and a year, see earnings and the rate card. */
export function DashboardApp() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerId, setProviderId] = useState<number | null>(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [rateCard, setRateCard] = useState<RateCardRow[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [detail, setDetail] = useState<MonthDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    earningsApi
      .providers()
      .then((list) => {
        setProviders(list);
        setProviderId((current) => current ?? list[0]?.id ?? null);
      })
      .catch((e: Error) => setError(`Can't reach the earnings API (port 8715): ${e.message}`));
  }, []);

  useEffect(() => {
    if (providerId === null) return;
    setSummary(null);
    setSelectedMonth(null);
    earningsApi
      .summary(providerId, year)
      .then((s) => {
        setSummary(s);
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, [providerId, year]);

  useEffect(() => {
    if (providerId === null) return;
    earningsApi
      .rateCard(providerId)
      .then(setRateCard)
      .catch((e: Error) => setError(e.message));
  }, [providerId]);

  useEffect(() => {
    setDetail(null);
    if (providerId === null || selectedMonth === null) return;
    earningsApi
      .month(providerId, selectedMonth)
      .then(setDetail)
      .catch((e: Error) => setError(e.message));
  }, [providerId, selectedMonth]);

  const bars = useMemo(() => (summary ? monthlyBars(summary.months, summary.year) : []), [summary]);

  return (
    <div className="dash">
      <header className="dash-header">
        <div className="dash-brand">
          <span className="dash-logo">A</span> Earnings
        </div>
        <div className="dash-pickers">
          <label>
            Signed in as
            <select value={providerId ?? ""} onChange={(e) => setProviderId(Number(e.target.value))}>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Year
            <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      {error && <div className="dash-error">{error}</div>}

      <main className="dash-main">
        <div className="dash-column">
          <section className="dash-card">
            {summary ? (
              <>
                <div className="dash-total">
                  <div>
                    <span className="muted">Earned in {summary.year}</span>
                    <strong>{formatCents(summary.total_cents)}</strong>
                  </div>
                  <div className="dash-total-side">
                    <span className="muted">Sessions</span>
                    <strong>{summary.session_count}</strong>
                  </div>
                </div>

                <h2>Earnings by month</h2>
                <div className="chart" role="list">
                  {bars.map((bar) => (
                    <button
                      key={bar.month}
                      role="listitem"
                      className={`chart-col ${bar.month === selectedMonth ? "active" : ""}`}
                      title={`${formatMonth(bar.month)}: ${formatCents(bar.earnedCents)} (${bar.sessionCount} sessions)`}
                      onClick={() => setSelectedMonth(bar.month)}
                    >
                      <span className="chart-value">{bar.earnedCents ? formatCents(bar.earnedCents).replace(/\.00$/, "") : ""}</span>
                      <span className="chart-track">
                        <span className="chart-bar" style={{ height: `${barHeight(bar, bars)}%` }} />
                      </span>
                      <span className="chart-label">{bar.label}</span>
                    </button>
                  ))}
                </div>

                <h3>By payer</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Payer</th>
                      <th className="num">Sessions</th>
                      <th className="num">Earned</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.by_payer.map((p) => (
                      <tr key={p.payer}>
                        <td>{p.payer}</td>
                        <td className="num">{p.session_count}</td>
                        <td className="num">{formatCents(p.earned_cents)}</td>
                      </tr>
                    ))}
                    {summary.by_payer.length === 0 && (
                      <tr>
                        <td colSpan={3} className="muted">
                          No sessions in {summary.year} yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </>
            ) : (
              <p className="muted">Loading earnings…</p>
            )}
          </section>

          {selectedMonth && (
            <section className="dash-card">
              <div className="detail-head">
                <h2>{formatMonth(selectedMonth)}</h2>
                {detail && (
                  <span className="muted">
                    {detail.session_count} session{detail.session_count === 1 ? "" : "s"} ·{" "}
                    <strong>{formatCents(detail.total_cents)}</strong>
                  </span>
                )}
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Client</th>
                    <th>Service</th>
                    <th>Payer</th>
                    <th>Paid</th>
                    <th className="num">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {detail?.lines.map((line) => (
                    <tr key={line.appointment_id}>
                      <td>
                        {formatDate(line.service_date)} <span className="muted">{formatTime(line.start_time)}</span>
                      </td>
                      <td>{line.client_name}</td>
                      <td>{serviceLabel(line.cpt_code)}</td>
                      <td>{line.payer}</td>
                      <td className="muted">{line.paid_on ? formatDate(line.paid_on) : "Pending"}</td>
                      <td className="num">{formatCents(line.rate_cents)}</td>
                    </tr>
                  ))}
                  {detail && detail.lines.length === 0 && (
                    <tr>
                      <td colSpan={6} className="muted">
                        No paid sessions this month.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          )}
        </div>

        <section className="dash-card rate-card">
          <h2>Your rates</h2>
          <p className="muted">What Acme Health pays you per session, by payer.</p>
          <table>
            <thead>
              <tr>
                <th>Payer</th>
                <th>Service</th>
                <th className="num">Rate</th>
              </tr>
            </thead>
            <tbody>
              {rateCard.map((row) => (
                <tr key={`${row.payer}-${row.cpt_code}`}>
                  <td>{row.payer}</td>
                  <td>{serviceLabel(row.cpt_code)}</td>
                  <td className="num">
                    {row.current ? (
                      <>
                        {formatCents(row.current.rate_cents)}
                        <span className="muted block">since {formatDate(row.current.effective_date, true)}</span>
                      </>
                    ) : (
                      <span className="muted">—</span>
                    )}
                    {row.upcoming && (
                      <span className="upcoming block">
                        {formatCents(row.upcoming.rate_cents)} from {formatDate(row.upcoming.effective_date, true)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}
