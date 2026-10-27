import { useCallback, useEffect, useState } from "react";
import { trainerApi, type ExerciseSummary, type Meta } from "./api";
import { CheatSheet } from "./components/CheatSheet";
import { ClinicApp } from "./components/ClinicApp";
import { ExerciseList } from "./components/ExerciseList";
import { ExerciseView } from "./components/ExerciseView";
import { InterviewView } from "./components/InterviewView";

type Route = { page: "exercises"; id: string | null } | { page: "cheatsheet" } | { page: "clinic" };

function parseHash(): Route {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "cheatsheet") return { page: "cheatsheet" };
  if (hash === "clinic") return { page: "clinic" };
  const match = hash.match(/^ex\/(\w+)$/);
  return { page: "exercises", id: match ? match[1] : null };
}

function daysUntil(isoDate: string): number {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const [y, m, d] = isoDate.split("-").map(Number);
  return Math.round((new Date(y, m - 1, d).getTime() - start.getTime()) / 86_400_000);
}

/** The top-bar countdown. Click it to pick (or clear) your interview date on a calendar. */
function InterviewCountdown({ date, onChange }: { date: string | null; onChange: (date: string | null) => void }) {
  const [editing, setEditing] = useState(false);
  const days = date ? daysUntil(date) : null;
  const label =
    days === null
      ? "📅 Set interview date"
      : days > 0
        ? `${days} day${days === 1 ? "" : "s"} to interview`
        : days === 0
          ? "Interview day: good luck!"
          : "Interview done";
  return (
    <span className="countdown-wrap">
      <button
        className={`countdown ${days === null ? "unset" : ""}`}
        title={date ? `Interview on ${date}. Click to change.` : "Pick your interview date for a countdown"}
        onClick={() => setEditing((v) => !v)}
      >
        {label}
      </button>
      {editing && (
        <span className="countdown-editor">
          <label>
            Interview date{" "}
            <input
              type="date"
              autoFocus
              defaultValue={date ?? ""}
              onChange={(e) => {
                if (e.target.value) {
                  onChange(e.target.value);
                  setEditing(false);
                }
              }}
            />
          </label>
          {date && (
            <button
              onClick={() => {
                onChange(null);
                setEditing(false);
              }}
            >
              Clear
            </button>
          )}
          <button onClick={() => setEditing(false)}>Close</button>
        </span>
      )}
    </span>
  );
}

export default function App() {
  const [route, setRoute] = useState<Route>(parseHash);
  const [exercises, setExercises] = useState<ExerciseSummary[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onHash = () => setRoute(parseHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const refreshList = useCallback(() => {
    trainerApi
      .list()
      .then((list) => {
        setExercises(list);
        setError(null);
      })
      .catch(() => setError("Can't reach the trainer API on port 8710. Is `npm run dev` (start.cmd) running?"));
  }, []);

  useEffect(() => {
    refreshList();
  }, [refreshList]);

  // The API may still be booting when the browser opens: keep retrying until it answers.
  useEffect(() => {
    if (meta && !error) return;
    const load = () => trainerApi.meta().then(setMeta).then(refreshList).catch(() => undefined);
    if (!meta) void load();
    const timer = window.setInterval(load, 2000);
    return () => window.clearInterval(timer);
  }, [meta, error, refreshList]);

  const done = exercises.filter((e) => e.status === "completed").length;
  const selectedId = route.page === "exercises" ? (route.id ?? exercises[0]?.id ?? null) : null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">py</span>
          <span>Interview Trainer</span>
        </div>
        <nav className="tabs">
          <a className={route.page === "exercises" ? "active" : ""} href={selectedId ? `#/ex/${selectedId}` : "#/"}>
            Exercises
          </a>
          <a className={route.page === "cheatsheet" ? "active" : ""} href="#/cheatsheet">
            TS → Python
          </a>
          <a className={route.page === "clinic" ? "active" : ""} href="#/clinic">
            Clinic App
          </a>
        </nav>
        <div className="topbar-stats">
          <div className="progress-pill" title="Completed exercises">
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{ width: `${exercises.length ? (done / exercises.length) * 100 : 0}%` }}
              />
            </div>
            <span>
              {done}/{exercises.length || 20} done
            </span>
          </div>
          {meta && (
            <InterviewCountdown
              date={meta.interview_date}
              onChange={(date) =>
                void trainerApi
                  .saveInterviewDate(date)
                  .then((s) => setMeta((m) => (m ? { ...m, interview_date: s.interview_date } : m)))
                  .catch((e: Error) => setError(e.message))
              }
            />
          )}
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      {route.page === "exercises" && (
        <div className="layout">
          <ExerciseList exercises={exercises} selectedId={selectedId} />
          <main className="content">
            {selectedId && exercises.find((e) => e.id === selectedId)?.track === "interview" ? (
              <InterviewView key={selectedId} scenario={selectedId} />
            ) : selectedId ? (
              <ExerciseView key={selectedId} id={selectedId} meta={meta} exercises={exercises} onChanged={refreshList} />
            ) : (
              <p className="muted">Loading exercises…</p>
            )}
          </main>
        </div>
      )}
      {route.page === "cheatsheet" && <CheatSheet />}
      {route.page === "clinic" && <ClinicApp />}
    </div>
  );
}
