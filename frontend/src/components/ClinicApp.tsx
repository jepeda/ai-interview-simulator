import { useCallback, useEffect, useState } from "react";
import { clinicApi, describeError } from "../clinic/clinicApi";
import { applyPatientUpdate } from "../clinic/patientState";
import type { Appointments, Eligibility, Patient, Plan } from "../clinic/types";

const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time

const ELIGIBILITY_LABEL: Record<Eligibility["status"], string> = {
  eligible: "Eligible",
  not_yet_active: "Not yet active",
  terminated: "Terminated",
  no_coverage: "No coverage",
};

/**
 * A tiny front-desk UI for the clinic API. It's here so you can SEE the debugging-challenge
 * bugs (dbg1–dbg5) the way a user would, then confirm your fixes end to end.
 */
export function ClinicApp() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [payer, setPayer] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(() => {
    clinicApi
      .listPatients({ includeArchived, payer })
      .then((page) => {
        setPatients(page.items);
        setTotal(page.total);
        setError(null);
      })
      .catch((e) => setError(describeError(e).join("; ")));
  }, [includeArchived, payer]);

  useEffect(loadList, [loadList]);
  useEffect(() => {
    clinicApi.plans().then(setPlans).catch(() => undefined);
  }, []);

  if (error && patients.length === 0) {
    return (
      <div className="pad">
        <div className="banner error">
          Clinic API unavailable ({error}). It runs on port 8711 from <code>backend/workspace/clinic</code>. If you
          introduced a syntax error, the <strong>clinic</strong> terminal shows the traceback; it reloads when you save.
        </div>
        <button onClick={loadList}>Retry</button>
      </div>
    );
  }

  return (
    <div className="clinic">
      <section className="card clinic-list">
        <div className="clinic-toolbar">
          <h2>
            Patients <span className="muted small">({total})</span>
          </h2>
          <button className="primary" onClick={() => setShowCreate((s) => !s)}>
            {showCreate ? "Close form" : "+ New patient"}
          </button>
        </div>
        <div className="filters">
          <select value={payer} onChange={(e) => setPayer(e.target.value)}>
            <option value="">All payers</option>
            {[...new Set(plans.map((p) => p.payer_name))].map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
          <label>
            <input type="checkbox" checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)} />{" "}
            Include archived
          </label>
          <button className="ghost" onClick={loadList}>
            Refresh
          </button>
        </div>
        {showCreate && (
          <CreatePatientForm
            plans={plans}
            onCreated={(p) => {
              setShowCreate(false);
              loadList();
              setSelectedId(p.id);
            }}
          />
        )}
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Payer</th>
              <th>Member id</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id} className={p.id === selectedId ? "selected" : ""} onClick={() => setSelectedId(p.id)}>
                <td>
                  {p.last_name}, {p.first_name}
                </td>
                <td>{p.insurance_plan?.payer_name ?? <span className="muted">Self-pay</span>}</td>
                <td>{p.member_id ?? <span className="muted">—</span>}</td>
                <td>{p.status ?? <span className="muted">legacy</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">Expected with the demo data: 10 patients (11 with archived).</p>
      </section>

      <section className="clinic-detail">
        {selectedId === null ? (
          <div className="card muted">Select a patient.</div>
        ) : (
          <PatientDetail
            key={selectedId}
            id={selectedId}
            plans={plans}
            onUpdated={(updated) => setPatients((prev) => applyPatientUpdate(prev, updated))}
          />
        )}
      </section>
    </div>
  );
}

function PatientDetail({ id, plans, onUpdated }: { id: number; plans: Plan[]; onUpdated: (p: Patient) => void }) {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [eligibility, setEligibility] = useState<Eligibility | null>(null);
  const [appointments, setAppointments] = useState<Appointments | null>(null);
  const [onDate, setOnDate] = useState(today());
  const [errors, setErrors] = useState<string[]>([]);
  const [editing, setEditing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(() => {
    setErrors([]);
    clinicApi.patient(id).then(setPatient).catch((e) => setErrors(describeError(e)));
    clinicApi.appointments(id).then(setAppointments).catch((e) => setErrors(describeError(e)));
  }, [id]);

  useEffect(load, [load]);
  useEffect(() => {
    clinicApi.eligibility(id, onDate).then(setEligibility).catch((e) => setErrors(describeError(e)));
  }, [id, onDate, patient]);

  if (!patient) return <div className="card muted">{errors.length ? errors.join("; ") : "Loading…"}</div>;

  return (
    <>
      <div className="card">
        <div className="clinic-toolbar">
          <h2>
            {patient.first_name} {patient.last_name}
          </h2>
          <button onClick={() => setEditing((e) => !e)}>{editing ? "Cancel" : "Edit coverage"}</button>
        </div>
        {toast && <div className="banner info">{toast}</div>}
        {errors.length > 0 && <div className="banner error">{errors.join("; ")}</div>}
        <dl className="facts">
          <dt>Date of birth</dt>
          <dd>{patient.date_of_birth}</dd>
          <dt>Email</dt>
          <dd>{patient.email}</dd>
          <dt>Plan</dt>
          <dd>
            {patient.insurance_plan ? (
              `${patient.insurance_plan.payer_name} · ${patient.insurance_plan.plan_name}`
            ) : (
              <span className="muted">Self-pay</span>
            )}
          </dd>
          <dt>Coverage dates</dt>
          <dd>
            {patient.insurance_plan
              ? `${patient.insurance_plan.effective_date} → ${patient.insurance_plan.termination_date ?? "open-ended"}`
              : "—"}
          </dd>
          <dt>Member id</dt>
          <dd>{patient.member_id ?? "—"}</dd>
        </dl>
        {editing && (
          <CoverageForm
            patient={patient}
            plans={plans}
            onSaved={(updated) => {
              setPatient(updated);
              onUpdated(updated);
              setEditing(false);
              setToast("Coverage saved.");
            }}
          />
        )}
      </div>

      <div className="card">
        <div className="clinic-toolbar">
          <h2>Eligibility</h2>
          <input type="date" value={onDate} onChange={(e) => setOnDate(e.target.value)} />
        </div>
        {eligibility && (
          <p>
            <span className={`elig ${eligibility.status}`}>{ELIGIBILITY_LABEL[eligibility.status] ?? eligibility.status}</span>{" "}
            <span className="muted">{eligibility.reason}</span>
          </p>
        )}
      </div>

      <div className="card">
        <h2>Appointments</h2>
        {appointments && (
          <div className="appts">
            <AppointmentTable title="Upcoming" rows={appointments.upcoming} />
            <AppointmentTable title="Past" rows={appointments.past} />
          </div>
        )}
      </div>
    </>
  );
}

function AppointmentTable({ title, rows }: { title: string; rows: Appointments["upcoming"] }) {
  return (
    <div>
      <h3>{title}</h3>
      {rows.length === 0 ? (
        <p className="muted small">None</p>
      ) : (
        <table className="table compact">
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.status === "cancelled" ? "cancelled" : ""}>
                <td>{r.display_time}</td>
                <td>{r.provider_name}</td>
                <td className="muted">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function CoverageForm({ patient, plans, onSaved }: { patient: Patient; plans: Plan[]; onSaved: (p: Patient) => void }) {
  const [planId, setPlanId] = useState<string>(patient.insurance_plan ? String(patient.insurance_plan.id) : "");
  const [memberId, setMemberId] = useState(patient.member_id ?? "");
  const [errors, setErrors] = useState<string[]>([]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    try {
      const updated = await clinicApi.updateCoverage(patient.id, {
        insurance_plan_id: planId ? Number(planId) : null,
        member_id: planId ? memberId || null : null,
      });
      onSaved(updated);
    } catch (err) {
      setErrors(describeError(err));
    }
  }

  return (
    <form className="form" onSubmit={save}>
      <label>
        Plan
        <select value={planId} onChange={(e) => setPlanId(e.target.value)}>
          <option value="">None (self-pay)</option>
          {plans.map((p) => (
            <option key={p.id} value={p.id}>
              {p.payer_name} · {p.plan_name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Member id
        <input value={memberId} onChange={(e) => setMemberId(e.target.value)} disabled={!planId} />
      </label>
      {errors.length > 0 && <div className="banner error">{errors.join("; ")}</div>}
      <button className="primary" type="submit">
        Save coverage
      </button>
    </form>
  );
}

function CreatePatientForm({ plans, onCreated }: { plans: Plan[]; onCreated: (p: Patient) => void }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    email: "",
    insurance_plan_id: "",
    member_id: "",
  });
  const [errors, setErrors] = useState<string[]>([]);
  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [key]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    // Send exactly what the user typed (as a real client would); validation is the API's job.
    const body: Record<string, unknown> = {
      first_name: form.first_name,
      last_name: form.last_name,
      date_of_birth: form.date_of_birth,
      email: form.email,
    };
    if (form.insurance_plan_id) body.insurance_plan_id = Number(form.insurance_plan_id);
    if (form.member_id) body.member_id = form.member_id;
    try {
      onCreated(await clinicApi.createPatient(body));
    } catch (err) {
      setErrors(describeError(err));
    }
  }

  return (
    <form className="form create" onSubmit={submit}>
      <label>
        First name
        <input value={form.first_name} onChange={set("first_name")} />
      </label>
      <label>
        Last name
        <input value={form.last_name} onChange={set("last_name")} />
      </label>
      <label>
        Date of birth <span className="muted small">(YYYY-MM-DD)</span>
        <input value={form.date_of_birth} onChange={set("date_of_birth")} placeholder="1990-04-12" />
      </label>
      <label>
        Email
        <input value={form.email} onChange={set("email")} />
      </label>
      <label>
        Plan
        <select value={form.insurance_plan_id} onChange={set("insurance_plan_id")}>
          <option value="">None (self-pay)</option>
          {plans.map((p) => (
            <option key={p.id} value={p.id}>
              {p.payer_name} · {p.plan_name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Member id
        <input value={form.member_id} onChange={set("member_id")} />
      </label>
      {errors.length > 0 && (
        <ul className="banner error errors">
          {errors.map((m, i) => (
            <li key={i}>{m}</li>
          ))}
        </ul>
      )}
      <button className="primary" type="submit">
        Create patient
      </button>
    </form>
  );
}
