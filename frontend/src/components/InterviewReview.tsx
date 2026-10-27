import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { interviewApi, type ActivitySummary, type InterviewEvent, type InterviewSnapshot } from "../api";
import { InterviewAttempts } from "./InterviewAttempts";
import { clock } from "./interviewClock";

function describe(e: InterviewEvent): { icon: string; text: string; detail?: string } {
  switch (e.kind) {
    case "start":
      return { icon: "▶", text: "Interview started" };
    case "prompt":
      return { icon: e.persona === "assistant" ? "🤖" : "🧑‍💼", text: `You → ${e.persona === "assistant" ? "AI assistant" : "interviewer"}`, detail: String(e.text) };
    case "reply": {
      const tools = (e.tools as { name: string; target: string }[]) ?? [];
      const toolText = tools.length ? ` · ${tools.map((t) => `${t.name} ${t.target.split("/").pop()}`).join(", ")}` : "";
      return {
        icon: "↩",
        text: `${e.persona === "assistant" ? "AI assistant" : "Interviewer"} replied${toolText}`,
        detail: String(e.text ?? ""),
      };
    }
    case "test_run": {
      const [bp, bt] = (e.bug as number[]) ?? [0, 0];
      const feat = e.feature as number[] | null;
      return { icon: "🧪", text: `Ran tests: bug ${bp}/${bt}${feat ? ` · feature ${feat[0]}/${feat[1]}` : ""}`, detail: ((e.failing as string[]) ?? []).join("\n") || undefined };
    }
    case "bug_fixed":
      return { icon: "✅", text: "Bug tests all passing: feature requests unlocked" };
    case "feature_chosen":
      return { icon: "📌", text: `Chose feature: ${String(e.feature)}` };
    case "feature_done":
      return { icon: "🏁", text: `Feature tests passing: ${String(e.feature)}` };
    case "code_change": {
      const files = (e.files as { path: string; added: number; removed: number }[]) ?? [];
      const what = files.map((f) => `${f.path.split("/").pop()} (+${f.added} −${f.removed})`).join(", ");
      return { icon: e.source === "ai" ? "🤖" : "✍️", text: `${e.source === "ai" ? "AI edited" : "You edited"} ${what}`, detail: String(e.diff ?? "") };
    }
    case "idle":
      return { icon: "💤", text: `${e.away ? "Away from the window" : "No input"} for ${clock(Number(e.seconds))}` };
    case "pause":
      return { icon: "⏸", text: "Paused the clock" };
    case "resume":
      return { icon: "▶", text: `Resumed after ${clock(Number(e.paused_for ?? 0))}` };
    case "data_reset":
      return { icon: "⟲", text: "Reset the demo data (reseeded with the current code)" };
    case "note":
      return { icon: e.source === "voice" ? "🎙" : "💬", text: String(e.text) };
    case "end":
      return { icon: "■", text: `Ended (${String(e.reason)})` };
    default:
      return { icon: "·", text: e.kind };
  }
}

export function InterviewReview({
  snapshot,
  onGraded,
  onRestart,
}: {
  snapshot: InterviewSnapshot;
  onGraded: () => void;
  onRestart: (s: InterviewSnapshot) => void;
}) {
  const session = snapshot.session!;
  const { config, scenarios } = snapshot;
  const next = scenarios.find((s) => !s.sandbox && s.order > config.order);
  const [grade, setGrade] = useState<string | null>(session.grade);
  const [grading, setGrading] = useState(false);
  const [gradeError, setGradeError] = useState<string | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [tab, setTab] = useState<"timeline" | "diff">("timeline");
  const [graded, setGraded] = useState(0);

  const [activity, setActivity] = useState<ActivitySummary | null>(null);
  useEffect(() => {
    interviewApi.diff().then((d) => setDiff(d.diff)).catch(() => setDiff(""));
    interviewApi.activitySummary().then(setActivity).catch(() => undefined);
  }, []);

  const events = session.events.filter((e) => e.kind !== "activity");
  const prompts = events.filter((e) => e.kind === "prompt");
  const toAssistant = prompts.filter((e) => e.persona === "assistant").length;
  const runs = events.filter((e) => e.kind === "test_run").length;
  const notes = events.filter((e) => e.kind === "note").length;
  const changed = (source: string) =>
    events
      .filter((e) => e.kind === "code_change" && e.source === source)
      .flatMap((e) => (e.files as { added: number; removed: number }[]) ?? [])
      .reduce((n, f) => n + f.added + f.removed, 0);
  const manualLines = changed("manual");
  const aiLines = changed("ai");
  const fixedAt = events.find((e) => e.kind === "bug_fixed")?.elapsed;
  const featureAt = events.find((e) => e.kind === "feature_done")?.elapsed;
  const feature = config.features.find((f) => f.id === session.feature_id);

  function runGrade() {
    setGrading(true);
    setGradeError(null);
    setGrade("");
    void interviewApi
      .grade((e) => {
        if (e.type === "text") setGrade((g) => (g ?? "") + e.text);
        else if (e.type === "error") setGradeError(e.message);
        else if (e.type === "done" && e.text) setGrade(e.text);
      })
      .finally(() => {
        setGrading(false);
        setGraded((n) => n + 1);
        onGraded();
      });
  }

  return (
    <article className="exercise interview-review">
      <header className="exercise-header">
        <div className="exercise-title">
          <div className="eyebrow">
            {config.sandbox ? "Sandbox" : `Mock AI interview #${config.order}`} · review · session {session.session_id}
          </div>
          <h1>{config.title}</h1>
        </div>
        <div className="header-actions">
          {next && (
            <a className="button-link" href={`#/ex/${next.id}`} title={next.title}>
              Next: interview #{next.order} →
            </a>
          )}
          <button
            className={next ? "" : "primary"}
            onClick={() => {
              if (window.confirm("Start a new interview? The payouts codebase is reset to the starter (this session's diff stays saved in the log)."))
                void interviewApi.start(config.id, true).then(onRestart);
            }}
          >
            ↻ Retry this one
          </button>
        </div>
      </header>

      <section className="stat-row">
        <div className="stat">
          <span className="stat-value">{clock(session.elapsed)}</span>
          <span className="stat-label">total time</span>
        </div>
        <div className={`stat ${fixedAt !== undefined ? "good" : "bad"}`}>
          <span className="stat-value">{fixedAt !== undefined ? clock(fixedAt) : "not fixed"}</span>
          <span className="stat-label">bug fixed at</span>
        </div>
        <div className={`stat ${featureAt !== undefined ? "good" : ""}`}>
          <span className="stat-value">{featureAt !== undefined ? clock(featureAt) : feature ? "in progress" : "–"}</span>
          <span className="stat-label">{feature ? feature.title : "feature"}</span>
        </div>
        <div className="stat">
          <span className="stat-value">{toAssistant} / {prompts.length - toAssistant}</span>
          <span className="stat-label">prompts to AI / interviewer</span>
        </div>
        <div className="stat">
          <span className="stat-value">{runs}</span>
          <span className="stat-label">test runs</span>
        </div>
        <div className="stat" title="Lines added + removed: by hand / by the AI assistant">
          <span className="stat-value">
            {manualLines} / {aiLines}
          </span>
          <span className="stat-label">lines changed by you / AI</span>
        </div>
        <div className={`stat ${notes === 0 ? "bad" : ""}`}>
          <span className="stat-value">{notes}</span>
          <span className="stat-label">narration notes</span>
        </div>
      </section>

      <section className="card">
        <h2>Grade</h2>
        {grade ? (
          <div className="markdown grade">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{grade}</ReactMarkdown>
          </div>
        ) : (
          <p className="muted">
            Claude reviews the whole log (prompts, replies, test runs, narration) and your final diff against the interview's criteria: debugging,
            code quality, verification, AI collaboration, communication, product thinking and time management.
          </p>
        )}
        {gradeError && <div className="banner error">{gradeError}</div>}
        <button className={grade ? "" : "primary"} disabled={grading} onClick={runGrade}>
          {grading ? "Grading… (about a minute)" : grade ? "Grade again" : "Grade my interview"}
        </button>
      </section>

      {activity && activity.targets.length > 0 && <TimeSpent activity={activity} />}

      <InterviewAttempts highlight={session.session_id} refreshKey={graded} />

      <section className="card">
        <div className="panel-tabs">
          <button className={tab === "timeline" ? "active" : ""} onClick={() => setTab("timeline")}>
            Timeline ({events.length})
          </button>
          <button className={tab === "diff" ? "active" : ""} onClick={() => setTab("diff")}>
            Your changes
          </button>
        </div>
        {tab === "timeline" ? (
          <ol className="timeline full">
            {events.map((e, i) => {
              const d = describe(e);
              return (
                <li key={i} className={`ev-${e.kind}`}>
                  <span className="stamp">{clock(e.elapsed)}</span>
                  <span className="ev-icon">{d.icon}</span>
                  <div className="ev-body">
                    <div>{d.text}</div>
                    {d.detail &&
                      (e.kind === "code_change" ? (
                        <details>
                          <summary className="muted small">show diff</summary>
                          <DiffView diff={d.detail} />
                        </details>
                      ) : e.kind === "reply" ? (
                        <details>
                          <summary className="muted small">show reply</summary>
                          <div className="markdown">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{d.detail}</ReactMarkdown>
                          </div>
                        </details>
                      ) : (
                        <pre className="ev-detail">{d.detail}</pre>
                      ))}
                  </div>
                </li>
              );
            })}
          </ol>
        ) : diff === null ? (
          <p className="muted">Loading…</p>
        ) : diff ? (
          <DiffView diff={diff} />
        ) : (
          <p className="muted">No changes to the codebase.</p>
        )}
      </section>
    </article>
  );
}

function DiffView({ diff }: { diff: string }) {
  return (
    <pre className="diff">
      {diff.split("\n").map((line, i) => (
        <span key={i} className={line.startsWith("+") && !line.startsWith("+++") ? "add" : line.startsWith("-") && !line.startsWith("---") ? "del" : line.startsWith("@@") ? "hunk" : ""}>
          {line + "\n"}
        </span>
      ))}
    </pre>
  );
}

const PANEL_LABELS: Record<string, string> = {
  ticket: "Ticket / features",
  assistant: "AI assistant chat",
  interviewer: "Interviewer chat",
  tests: "Test results",
  app: "The app",
  notes: "Narration",
};

function targetLabel(target: string): string {
  if (target.startsWith("file:")) return target.slice(5).split("/").slice(-2).join("/");
  if (target.startsWith("panel:")) return PANEL_LABELS[target.slice(6)] ?? target.slice(6);
  return target === "header" ? "Header (run tests, timer)" : target;
}

/** Where the time went: active seconds per file / panel, idle and away time, input counts. */
function TimeSpent({ activity }: { activity: ActivitySummary }) {
  const total = activity.active + activity.idle + activity.away || 1;
  const rows = [
    ...activity.targets.slice(0, 14).map((t) => ({
      key: t.target,
      label: targetLabel(t.target),
      kind: t.target.startsWith("file:") ? "file" : "panel",
      seconds: t.seconds,
      detail: `${t.keys} keys · ${t.clicks} clicks · ${t.scrolls} scrolls`,
    })),
    { key: "idle", label: "Idle (no input 45s+)", kind: "idle", seconds: activity.idle, detail: "" },
    { key: "away", label: "Away from the window", kind: "idle", seconds: activity.away, detail: "" },
  ].filter((r) => r.seconds > 0);
  const max = Math.max(...rows.map((r) => r.seconds), 1);
  return (
    <section className="card">
      <h2>Where your time went</h2>
      <p className="muted small">
        Active {clock(activity.active)} · idle {clock(activity.idle)} · away {clock(activity.away)} · {activity.keys} keys, {activity.clicks} clicks,{" "}
        {activity.scrolls} scrolls. Attention goes to wherever your last click, key, scroll or mouse move was; reading counts as active for 45s
        after your last input.
      </p>
      <ul className="time-bars">
        {rows.map((r) => (
          <li key={r.key} title={r.detail}>
            <span className="time-label">{r.label}</span>
            <span className="time-bar">
              <span className={`fill ${r.kind}`} style={{ width: `${(r.seconds / max) * 100}%` }} />
            </span>
            <span className="time-value">
              {clock(r.seconds)} <span className="muted small">{Math.round((r.seconds / total) * 100)}%</span>
            </span>
          </li>
        ))}
      </ul>
      {activity.files_opened.length > 0 && (
        <details>
          <summary className="muted small">Files in the order you opened them ({activity.files_opened.length})</summary>
          <ol className="opened-files small">
            {activity.files_opened.map((f) => (
              <li key={f.path}>
                <span className="stamp">{clock(f.at)}</span> <code>{f.path}</code>
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
