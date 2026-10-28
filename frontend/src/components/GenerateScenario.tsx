import { useCallback, useEffect, useState } from "react";
import { generateApi, type GenerateJob } from "../api";
import { clock } from "./interviewClock";

const DIFFICULTIES: { id: GenerateJob["difficulty"]; label: string }[] = [
  { id: "warmup", label: "Warmup (bug in ~15 min)" },
  { id: "standard", label: "Standard (like #1–#3)" },
  { id: "hard", label: "Hard (more layers, an edge-case trap)" },
];

function since(iso: string, until?: string | null): string {
  const end = until ? new Date(until).getTime() : Date.now();
  return clock(Math.max(0, Math.floor((end - new Date(iso).getTime()) / 1000)));
}

/**
 * "Generate a new scenario": Claude Code builds a fresh app with a bug, tests, a reference solution
 * and feature requests, optionally modeled on a company's product. It only shows up in the list once
 * it passes the content check. Progress never reveals the bug.
 */
export function GenerateScenario() {
  const [jobs, setJobs] = useState<GenerateJob[]>([]);
  const [company, setCompany] = useState("");
  const [domain, setDomain] = useState("");
  const [minutes, setMinutes] = useState<30 | 60>(60);
  const [difficulty, setDifficulty] = useState<GenerateJob["difficulty"]>("standard");
  const [error, setError] = useState<string | null>(null);
  const [, setTick] = useState(0);

  const load = useCallback(() => {
    generateApi
      .jobs()
      .then(setJobs)
      .catch(() => undefined);
  }, []);
  const busy = jobs.some((j) => j.status === "running" || j.status === "verifying");

  useEffect(() => {
    load();
    const timer = window.setInterval(() => {
      setTick((t) => t + 1);
      if (busy) load();
    }, busy ? 3000 : 1000);
    return () => window.clearInterval(timer);
  }, [busy, load]);

  return (
    <section className="card generate">
      <h2>Generate a new scenario</h2>
      <p className="muted small">
        Claude Code builds a fresh full-stack app with a user-reported bug, its tests, feature requests and a reference solution, then the
        trainer checks it (the starter must fail, the solution must pass) before it appears in the list. Name a company to practise on a slice
        of its product. You never see the bug until you start. Takes about 15–30 minutes and uses your Claude Code plan.
      </p>
      <form
        className="generate-form"
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          generateApi
            .start({ company, domain, minutes, difficulty })
            .then(() => {
              setCompany("");
              setDomain("");
              load();
            })
            .catch((err: Error) => setError(err.message));
        }}
      >
        <label>
          <span>
            Company <span className="muted small">(optional)</span>
          </span>
          <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. the company you're interviewing with" maxLength={80} />
        </label>
        <label>
          <span>
            What they do / what to focus on <span className="muted small">(optional)</span>
          </span>
          <input
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="e.g. insurance eligibility checks, appointment reminders…"
            maxLength={400}
          />
        </label>
        <label>
          Length
          <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value) as 30 | 60)}>
            <option value={30}>30 minutes</option>
            <option value={60}>60 minutes</option>
          </select>
        </label>
        <label>
          Difficulty
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value as GenerateJob["difficulty"])}>
            {DIFFICULTIES.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <button className="primary" disabled={busy}>
          {busy ? "Generating…" : "✨ Generate"}
        </button>
      </form>
      {error && <div className="banner error">{error}</div>}

      {jobs.length > 0 && (
        <ul className="generate-jobs">
          {jobs.map((j) => (
            <li key={j.id} className={`job ${j.status}`}>
              <div>
                <strong>{j.company || j.domain || "Surprise me"}</strong>{" "}
                <span className="muted small">
                  · {j.minutes} min · {j.difficulty}
                </span>
              </div>
              {(j.status === "running" || j.status === "verifying") && (
                <div className="muted small">
                  {j.status === "running" ? `Building… ${j.steps} steps${j.last_tool ? ` (last: ${j.last_tool})` : ""}` : "Checking: starter must fail, solution must pass…"} ·{" "}
                  {since(j.started_at)}
                </div>
              )}
              {j.status === "ready" && (
                <div className="small">
                  ✓ Ready in {since(j.started_at, j.finished_at)}: {j.title}{" "}
                  <button
                    className="primary"
                    onClick={() => {
                      window.location.hash = `#/ex/${j.pkg}`;
                      window.location.reload(); // reload the exercise list so it shows up
                    }}
                  >
                    Open
                  </button>{" "}
                  <button onClick={() => void generateApi.dismiss(j.id).then(load)}>Dismiss</button>
                </div>
              )}
              {j.status === "failed" && (
                <div className="small">
                  <span className="bad-text">✗ {j.error}</span> <button onClick={() => void generateApi.dismiss(j.id).then(load)}>Dismiss</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
