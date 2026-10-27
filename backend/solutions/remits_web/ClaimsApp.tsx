import { useCallback, useEffect, useState } from "react";
import {
  remitsApi,
  type Adjustment,
  type ClaimDetail,
  type ClaimStatus,
  type ClaimSummary,
  type DenialQueue,
  type RemittanceDetail,
  type RemittanceSummary,
  type SuspenseLine,
  type UnderpaymentReport,
} from "./api";
import { formatAccounting, formatDate, formatReceived, serviceLabel, statusLabel } from "./format";

type Tab = "claims" | "remittances" | "queues";

const TAB_LABELS: Record<Tab, string> = { claims: "Claims", remittances: "Remittances", queues: "Work queues" };
type OnError = (message: string | null) => void;

const STATUS_FILTERS: Array<ClaimStatus | ""> = ["", "submitted", "partially_paid", "paid", "overpaid", "denied"];

/** Billing-ops portal: claims and their balances, and the payer remittances (ERAs) posted to them. */
export function ClaimsApp() {
  const [tab, setTab] = useState<Tab>("claims");
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="portal">
      <header className="portal-header">
        <div className="portal-brand">
          <span className="portal-logo">A</span> Claims portal
          <span className="muted">Revenue cycle</span>
        </div>
        <nav className="portal-tabs">
          {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
            <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>
              {TAB_LABELS[t]}
            </button>
          ))}
        </nav>
      </header>
      {error && <div className="portal-error">{error}</div>}
      {tab === "claims" && <ClaimsView onError={setError} />}
      {tab === "remittances" && <RemittancesView onError={setError} />}
      {tab === "queues" && <WorkQueuesView onError={setError} />}
    </div>
  );
}

function Money({ cents, strong = false }: { cents: number; strong?: boolean }) {
  const text = formatAccounting(cents);
  const className = cents < 0 ? "negative" : "";
  return strong ? <strong className={className}>{text}</strong> : <span className={className}>{text}</span>;
}

function AdjustmentChips({ adjustments }: { adjustments: Adjustment[] }) {
  return (
    <span className="chips">
      {adjustments.map((a, i) => (
        <span key={i} className={`chip chip-${a.group_code.toLowerCase()}`} title={a.description}>
          {a.code} {formatAccounting(a.amount_cents)}
        </span>
      ))}
    </span>
  );
}

function ClaimsView({ onError }: { onError: OnError }) {
  const [status, setStatus] = useState<ClaimStatus | "">("");
  const [search, setSearch] = useState("");
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<ClaimDetail | null>(null);

  useEffect(() => {
    remitsApi
      .claims({ status: status || undefined, q: search.trim() || undefined })
      .then((list) => {
        setClaims(list);
        onError(null);
      })
      .catch((e: Error) => onError(`Can't load claims from the remits API (port 8714): ${e.message}`));
  }, [status, search, onError]);

  useEffect(() => {
    if (selected === null) return;
    remitsApi
      .claim(selected)
      .then(setDetail)
      .catch((e: Error) => onError(e.message));
  }, [selected, onError]);

  return (
    <main className="portal-main">
      <section className="portal-card">
        <div className="toolbar">
          <h2>Claims</h2>
          <input placeholder="Claim # or patient" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={status} onChange={(e) => setStatus(e.target.value as ClaimStatus | "")}>
            {STATUS_FILTERS.map((s) => (
              <option key={s} value={s}>
                {s ? statusLabel(s) : "All statuses"}
              </option>
            ))}
          </select>
        </div>
        <table className="clickable">
          <thead>
            <tr>
              <th>Claim</th>
              <th>Patient</th>
              <th>Payer</th>
              <th>DOS</th>
              <th className="num">Billed</th>
              <th className="num">Paid</th>
              <th className="num">Balance</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((c) => (
              <tr
                key={c.claim_number}
                className={c.claim_number === selected ? "active" : ""}
                onClick={() => setSelected(c.claim_number)}
              >
                <td className="mono">{c.claim_number}</td>
                <td>{c.patient_name}</td>
                <td>{c.payer}</td>
                <td>{formatDate(c.date_of_service)}</td>
                <td className="num">{formatAccounting(c.billed_cents)}</td>
                <td className="num">{formatAccounting(c.paid_cents)}</td>
                <td className="num">
                  <Money cents={c.balance_cents} />
                </td>
                <td>
                  <span className={`pill pill-${c.status}`}>{statusLabel(c.status)}</span>
                </td>
              </tr>
            ))}
            {claims.length === 0 && (
              <tr>
                <td colSpan={8} className="muted">
                  No claims match.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="portal-card">
        {detail ? <ClaimPanel claim={detail} /> : <p className="muted">Select a claim to see its payments.</p>}
      </section>
    </main>
  );
}

function ClaimPanel({ claim }: { claim: ClaimDetail }) {
  return (
    <>
      <div className="panel-head">
        <div>
          <h2>
            {claim.claim_number} <span className={`pill pill-${claim.status}`}>{statusLabel(claim.status)}</span>
          </h2>
          <p className="muted">
            {claim.patient_name} · {claim.provider_name} · {serviceLabel(claim.cpt_code)} · DOS{" "}
            {formatDate(claim.date_of_service)}
          </p>
        </div>
      </div>
      <dl className="figures">
        <div>
          <dt>Billed</dt>
          <dd>{formatAccounting(claim.billed_cents)}</dd>
        </div>
        <div>
          <dt>Contract allows</dt>
          <dd>{claim.contracted_allowed_cents === null ? "—" : formatAccounting(claim.contracted_allowed_cents)}</dd>
        </div>
        <div>
          <dt>{claim.payer} paid</dt>
          <dd>{formatAccounting(claim.paid_cents)}</dd>
        </div>
        <div>
          <dt>Patient owes</dt>
          <dd>{formatAccounting(claim.patient_resp_cents)}</dd>
        </div>
        <div>
          <dt>Written off</dt>
          <dd>{formatAccounting(claim.adjusted_cents)}</dd>
        </div>
        <div>
          <dt>Balance</dt>
          <dd>
            <Money cents={claim.balance_cents} strong />
          </dd>
        </div>
      </dl>

      <h3>Payments posted</h3>
      {claim.payments.length === 0 ? (
        <p className="muted">Nothing posted yet: waiting for {claim.payer}'s remittance.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Paid on</th>
              <th>Trace #</th>
              <th>Status</th>
              <th>Adjustments</th>
              <th className="num">Paid</th>
            </tr>
          </thead>
          <tbody>
            {claim.payments.map((p, i) => (
              <tr key={i}>
                <td>{formatDate(p.paid_on)}</td>
                <td className="mono">{p.trace_number}</td>
                <td className="muted">{p.status_description}</td>
                <td>
                  <AdjustmentChips adjustments={p.adjustments} />
                </td>
                <td className="num">
                  <Money cents={p.paid_cents} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

function RemittancesView({ onError }: { onError: OnError }) {
  const [remits, setRemits] = useState<RemittanceSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<RemittanceDetail | null>(null);

  useEffect(() => {
    remitsApi
      .remittances()
      .then((list) => {
        setRemits(list);
        setSelected((current) => current ?? list[0]?.id ?? null);
        onError(null);
      })
      .catch((e: Error) => onError(`Can't load remittances from the remits API (port 8714): ${e.message}`));
  }, [onError]);

  useEffect(() => {
    if (selected === null) return;
    remitsApi
      .remittance(selected)
      .then(setDetail)
      .catch((e: Error) => onError(e.message));
  }, [selected, onError]);

  return (
    <main className="portal-main narrow-left">
      <section className="portal-card remit-list">
        <h2>Remittances</h2>
        <ul>
          {remits.map((r) => (
            <li key={r.id}>
              <button className={r.id === selected ? "active" : ""} onClick={() => setSelected(r.id)}>
                <span>
                  {r.payer} · {r.payment_method} <span className="mono">{r.trace_number}</span>
                </span>
                <span className="muted">
                  Paid {formatDate(r.paid_on)} · {r.claim_count} claims
                </span>
                <strong>{formatAccounting(r.total_paid_cents)}</strong>
                {r.out_of_balance_cents !== 0 && <span className="flag">Out of balance</span>}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="portal-card">
        {detail ? <RemittancePanel remit={detail} /> : <p className="muted">No remittances yet.</p>}
      </section>
    </main>
  );
}

function RemittancePanel({ remit }: { remit: RemittanceDetail }) {
  return (
    <>
      <div className="panel-head">
        <div>
          <h2>
            {remit.payer} {remit.payment_method === "ACH" ? "EFT" : "check"} {remit.trace_number}
          </h2>
          <p className="muted">
            Paid {formatDate(remit.paid_on)} · file received {formatReceived(remit.received_at)} ET
          </p>
        </div>
      </div>
      <dl className="figures">
        <div>
          <dt>Payment total</dt>
          <dd>{formatAccounting(remit.total_paid_cents)}</dd>
        </div>
        <div>
          <dt>Posted</dt>
          <dd>{formatAccounting(remit.posted_cents)}</dd>
        </div>
        {remit.suspense_cents !== 0 && (
          <div>
            <dt>In suspense</dt>
            <dd>{formatAccounting(remit.suspense_cents)}</dd>
          </div>
        )}
        <div>
          <dt>Out of balance</dt>
          <dd className={remit.out_of_balance_cents !== 0 ? "negative" : ""}>
            {formatAccounting(remit.out_of_balance_cents)}
          </dd>
        </div>
      </dl>

      <h3>Claims</h3>
      <table>
        <thead>
          <tr>
            <th>Claim</th>
            <th>Patient</th>
            <th>Adjustments</th>
            <th className="num">Billed</th>
            <th className="num">Paid</th>
          </tr>
        </thead>
        <tbody>
          {remit.lines.map((line) => (
            <tr key={line.claim_number}>
              <td className="mono">{line.claim_number}</td>
              <td>{line.patient_name}</td>
              <td>
                <AdjustmentChips adjustments={line.adjustments} />
              </td>
              <td className="num">{formatAccounting(line.billed_cents)}</td>
              <td className="num">
                <Money cents={line.paid_cents} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {remit.remit_adjustments.length > 0 && (
        <>
          <h3>Remit-level adjustments</h3>
          <table>
            <tbody>
              {remit.remit_adjustments.map((a, i) => (
                <tr key={i}>
                  <td className="mono">{a.code}</td>
                  <td>
                    {a.description}
                    {a.reference && <span className="muted"> · {a.reference}</span>}
                  </td>
                  <td className="num">
                    <Money cents={a.amount_cents} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}

function WorkQueuesView({ onError }: { onError: OnError }) {
  const [denials, setDenials] = useState<DenialQueue | null>(null);
  const [underpaid, setUnderpaid] = useState<UnderpaymentReport | null>(null);
  const [suspense, setSuspense] = useState<SuspenseLine[]>([]);
  const [matchTo, setMatchTo] = useState<Record<number, string>>({});

  const load = useCallback(() => {
    Promise.all([remitsApi.denials(), remitsApi.underpayments(), remitsApi.suspense()])
      .then(([d, u, s]) => {
        setDenials(d);
        setUnderpaid(u);
        setSuspense(s);
        onError(null);
      })
      .catch((e: Error) => onError(e.message));
  }, [onError]);

  useEffect(load, [load]);

  const match = (line: SuspenseLine) => {
    const claimNumber = (matchTo[line.id] ?? "").trim();
    if (!claimNumber) return;
    remitsApi
      .matchSuspense(line.id, claimNumber)
      .then(load)
      .catch((e: Error) => onError(e.message));
  };

  return (
    <main className="portal-main queues">
      <section className="portal-card">
        <h2>Denials</h2>
        {denials && (
          <>
            <p className="chips">
              {Object.entries(denials.buckets).map(([bucket, count]) => (
                <span key={bucket} className="chip">
                  {bucket} days: <strong>{count}</strong>
                </span>
              ))}
            </p>
            <table>
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Payer</th>
                  <th>Reason</th>
                  <th>DOS</th>
                  <th className="num">Days</th>
                  <th className="num">Billed</th>
                </tr>
              </thead>
              <tbody>
                {denials.claims.map((d) => (
                  <tr key={d.claim_number}>
                    <td className="mono">{d.claim_number}</td>
                    <td>{d.payer}</td>
                    <td title={d.denial_reason}>{d.denial_code}</td>
                    <td>{formatDate(d.date_of_service)}</td>
                    <td className="num">{d.days_outstanding}</td>
                    <td className="num">{formatAccounting(d.billed_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      <section className="portal-card">
        <h2>Underpayments</h2>
        {underpaid && (
          <>
            <p className="muted">
              Allowed more than {formatAccounting(underpaid.tolerance_cents)} below contract · total{" "}
              {formatAccounting(underpaid.total_variance_cents)}
            </p>
            <table>
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Payer</th>
                  <th className="num">Contract</th>
                  <th className="num">Allowed</th>
                  <th className="num">Short</th>
                </tr>
              </thead>
              <tbody>
                {underpaid.claims.map((u) => (
                  <tr key={u.claim_number}>
                    <td className="mono">{u.claim_number}</td>
                    <td>{u.payer}</td>
                    <td className="num">{formatAccounting(u.expected_cents)}</td>
                    <td className="num">{formatAccounting(u.allowed_cents)}</td>
                    <td className="num negative">{formatAccounting(u.variance_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      <section className="portal-card">
        <h2>Suspense</h2>
        {suspense.length === 0 ? (
          <p className="muted">Every remittance line is matched to a claim.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Sent as</th>
                <th>Payment</th>
                <th className="num">Paid</th>
                <th>Match to claim</th>
              </tr>
            </thead>
            <tbody>
              {suspense.map((line) => (
                <tr key={line.id}>
                  <td className="mono">{line.claim_number}</td>
                  <td>
                    {line.payer} <span className="mono">{line.trace_number}</span>
                  </td>
                  <td className="num">{formatAccounting(line.paid_cents)}</td>
                  <td>
                    <input
                      placeholder="HW-…"
                      value={matchTo[line.id] ?? ""}
                      onChange={(e) => setMatchTo({ ...matchTo, [line.id]: e.target.value })}
                    />{" "}
                    <button onClick={() => match(line)}>Match</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
