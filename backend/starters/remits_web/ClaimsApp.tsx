import { useEffect, useState } from "react";
import {
  remitsApi,
  type Adjustment,
  type ClaimDetail,
  type ClaimStatus,
  type ClaimSummary,
  type RemittanceDetail,
  type RemittanceSummary,
} from "./api";
import { formatAccounting, formatDate, formatReceived, serviceLabel, statusLabel } from "./format";

type Tab = "claims" | "remittances";
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
          {(["claims", "remittances"] as const).map((t) => (
            <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>
              {t === "claims" ? "Claims" : "Remittances"}
            </button>
          ))}
        </nav>
      </header>
      {error && <div className="portal-error">{error}</div>}
      {tab === "claims" ? <ClaimsView onError={setError} /> : <RemittancesView onError={setError} />}
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
