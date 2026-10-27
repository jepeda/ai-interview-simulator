import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { interviewApi, type PastSession } from "../api";
import { clock } from "./interviewClock";

const VERDICT_CLASS: Record<string, string> = {
  "Strong hire": "good",
  Hire: "good",
  "Lean hire": "ok",
  "Lean no hire": "weak",
  "No hire": "bad",
};

/** Every attempt side by side (oldest first): timings, habits, and the grader's 1-4 scores. */
export function InterviewAttempts({ highlight, refreshKey = 0 }: { highlight?: string; refreshKey?: number }) {
  const [sessions, setSessions] = useState<PastSession[] | null>(null);
  useEffect(() => {
    interviewApi
      .sessions()
      .then((s) => setSessions(s.filter((x) => !x.sandbox).reverse()))
      .catch(() => setSessions([]));
  }, [refreshKey]);

  const [open, setOpen] = useState<{ id: string; grade: string | null; error?: string } | null>(null);
  function toggleGrade(id: string) {
    if (open?.id === id) return setOpen(null);
    setOpen({ id, grade: null });
    interviewApi
      .sessionGrade(id)
      .then((g) => setOpen((o) => (o?.id === id ? { id, grade: g.grade } : o)))
      .catch((e: Error) => setOpen((o) => (o?.id === id ? { id, grade: null, error: e.message } : o)));
  }

  if (!sessions || sessions.length === 0) return null;
  const dimensions = [...new Set(sessions.flatMap((s) => Object.keys(s.scores)))];
  const graded = sessions.filter((s) => s.graded && Object.keys(s.scores).length);

  return (
    <section className="card attempts">
      <h2>Your attempts</h2>
      <p className="muted small">
        Oldest first. Grade each attempt on its review screen so it shows up here; the grader also compares it with your earlier attempts.
      </p>
      <div className="attempts-scroll">
        <table className="attempts-table">
          <thead>
            <tr>
              <th />
              {sessions.map((s, i) => (
                <th key={s.session_id} className={s.session_id === highlight ? "current" : ""}>
                  <div>Attempt {i + 1}</div>
                  <div className="muted small">
                    #{s.order} · {s.session_id.slice(4, 8).replace(/(\d\d)(\d\d)/, "$1/$2")}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <Row label="Scenario" sessions={sessions} highlight={highlight} cell={(s) => <span className="small">{s.title || s.scenario}</span>} />
            <Row
              label="Verdict"
              sessions={sessions}
              highlight={highlight}
              cell={(s) => (s.verdict ? <span className={`verdict ${VERDICT_CLASS[s.verdict] ?? ""}`}>{s.verdict}</span> : <span className="muted">{s.ended ? "not graded" : "in progress"}</span>)}
            />
            <Row label="Bug fixed at" sessions={sessions} highlight={highlight} cell={(s) => (s.bug_fixed_at !== null ? clock(s.bug_fixed_at) : <span className="bad-text">✗</span>)} />
            <Row label="Feature done at" sessions={sessions} highlight={highlight} cell={(s) => (s.feature_done_at !== null ? clock(s.feature_done_at) : "–")} />
            <Row label="Total time" sessions={sessions} highlight={highlight} cell={(s) => clock(s.elapsed)} />
            <Row label="Prompts AI / interviewer" sessions={sessions} highlight={highlight} cell={(s) => `${s.assistant_prompts} / ${s.prompts - s.assistant_prompts}`} />
            <Row
              label="Active / idle or away"
              sessions={sessions}
              highlight={highlight}
              cell={(s) => (s.active_seconds || s.idle_seconds ? `${clock(s.active_seconds)} / ${clock(s.idle_seconds)}` : "–")}
            />
            <Row label="Lines changed by you / AI" sessions={sessions} highlight={highlight} cell={(s) => `${s.manual_lines} / ${s.ai_lines}`} />
            <Row label="Test runs" sessions={sessions} highlight={highlight} cell={(s) => s.test_runs} />
            <Row label="Narration notes" sessions={sessions} highlight={highlight} cell={(s) => (s.notes ? s.notes : <span className="bad-text">0</span>)} />
            {dimensions.map((d) => (
              <Row
                key={d}
                label={d}
                sessions={sessions}
                highlight={highlight}
                cell={(s) => (s.scores[d] ? <span className={`score s${s.scores[d]}`}>{s.scores[d]}</span> : "–")}
              />
            ))}
            {graded.length > 0 && (
              <Row
                label="Average score"
                sessions={sessions}
                highlight={highlight}
                cell={(s) => {
                  const values = Object.values(s.scores);
                  return values.length ? <strong>{(values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)}</strong> : "–";
                }}
              />
            )}
            {graded.length > 0 && (
              <Row
                label="Grade report"
                sessions={sessions}
                highlight={highlight}
                cell={(s) =>
                  s.graded ? (
                    <button className="small" onClick={() => toggleGrade(s.session_id)}>
                      {open?.id === s.session_id ? "Hide grade" : "View grade"}
                    </button>
                  ) : (
                    "–"
                  )
                }
              />
            )}
          </tbody>
        </table>
      </div>
      {open && (
        <div className="attempt-grade">
          <h3>
            Attempt {sessions.findIndex((s) => s.session_id === open.id) + 1} grade
            <button className="small" onClick={() => setOpen(null)}>
              Close
            </button>
          </h3>
          {open.error ? (
            <div className="banner error">{open.error}</div>
          ) : open.grade === null ? (
            <p className="muted">Loading…</p>
          ) : (
            <div className="markdown grade">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{open.grade}</ReactMarkdown>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function Row({
  label,
  sessions,
  highlight,
  cell,
}: {
  label: string;
  sessions: PastSession[];
  highlight?: string;
  cell: (s: PastSession) => React.ReactNode;
}) {
  return (
    <tr>
      <th scope="row">{label}</th>
      {sessions.map((s) => (
        <td key={s.session_id} className={s.session_id === highlight ? "current" : ""}>
          {cell(s)}
        </td>
      ))}
    </tr>
  );
}
