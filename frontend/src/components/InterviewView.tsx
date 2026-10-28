import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  generateApi,
  interviewApi,
  requirementsPath,
  setInterviewScenario,
  type InterviewEvent,
  type InterviewSnapshot,
  type Persona,
  type RunResult,
} from "../api";
import { CodeEditor, type CodeEditorHandle } from "../editor/CodeEditor";
import { readNumber, Splitter, store } from "../editor/Splitter";
import { useActivityTracker } from "./interviewActivity";
import { GenerateScenario } from "./GenerateScenario";
import { InterviewAttempts } from "./InterviewAttempts";
import { InterviewChat, messagesFromEvents } from "./InterviewChat";
import { clock, sessionElapsed } from "./interviewClock";
import { InterviewReview } from "./InterviewReview";
import { TestResults } from "./TestResults";

type Tab = "ticket" | "assistant" | "interviewer" | "tests" | "app" | "notes";
const TAB_KEY = "trainer.interviewTab";
const SIDE_KEY = "trainer.interviewSideWidth";
const SIDE_MIN = 320;

function phaseHint(elapsed: number, minutes: number, stage: string, featureChosen: boolean): string {
  const left = minutes * 60 - elapsed;
  if (left <= 0) return "Time's up. Wrap up out loud: what you fixed, how you verified it, what you'd do next.";
  if (left <= 5 * 60) return "Last 5 minutes: summarize your fix and trade-offs, and ask the interviewer your questions.";
  if (stage === "bug") {
    if (elapsed < 5 * 60) return "Read the ticket, reproduce it in the App tab, and say your first hypothesis out loud.";
    if (elapsed > (minutes / 2) * 60)
      return `Past ${minutes / 2} minutes on the bug. Narrow it down, and ask the interviewer if you're stuck.`;
    return "Debug: find the root cause, fix it, prove it with the tests and the app.";
  }
  if (!featureChosen) return "Bug fixed. Pick a feature request and tell the interviewer your plan before coding.";
  return "Build the feature in small, verified steps. Mention edge cases and trade-offs as you go.";
}

/** Browser speech-to-text (Chrome/Edge). Each final phrase becomes a logged narration note. */
type Recognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((e: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
};
const SpeechRecognitionCtor = (window as unknown as { webkitSpeechRecognition?: new () => Recognition; SpeechRecognition?: new () => Recognition })
  .SpeechRecognition ??
  (window as unknown as { webkitSpeechRecognition?: new () => Recognition }).webkitSpeechRecognition;

export function InterviewView({ scenario }: { scenario: string }) {
  setInterviewScenario(scenario); // before any request below (one interview view at a time)
  const [snap, setSnap] = useState<InterviewSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTabState] = useState<Tab>(() => {
    try {
      return (localStorage.getItem(TAB_KEY) as Tab) || "ticket";
    } catch {
      return "ticket";
    }
  });
  const [result, setResult] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  const [sideWidth, setSideWidth] = useState(() => readNumber(SIDE_KEY, Math.round(window.innerWidth * 0.36)));
  const dragStart = useRef(sideWidth);
  const [reloadToken, setReloadToken] = useState(0);
  const [appKey, setAppKey] = useState(0);
  const editorRef = useRef<CodeEditorHandle>(null);

  const setTab = (t: Tab) => {
    setTabState(t);
    store(TAB_KEY, t);
  };

  const load = useCallback(() => {
    interviewApi
      .get(scenario)
      .then((s) => {
        setSnap(s);
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, [scenario]);
  useEffect(load, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const session = snap?.session ?? null;
  const live = !!session && !session.ended_at;
  const paused = live && !!session?.paused_at;
  useActivityTracker({
    live: live && !paused,
    elapsed: () => (session ? sessionElapsed(session, Date.now()) : 0),
    tab,
    activePath: () => editorRef.current?.activePath() ?? null,
  });
  useEffect(() => {
    document.body.classList.toggle("no-scroll", live);
    return () => document.body.classList.remove("no-scroll");
  }, [live]);

  const appendEvent = (e: InterviewEvent) =>
    setSnap((s) => (s?.session ? { ...s, session: { ...s.session, events: [...s.session.events, e] } } : s));
  const mic = useMic(appendEvent, live && !paused);

  // While paused, nothing under the modal takes input: drop focus and swallow keys (the mouse is
  // already blocked by the overlay).
  useEffect(() => {
    if (!paused) return;
    (document.activeElement as HTMLElement | null)?.blur();
    const block = (e: KeyboardEvent) => {
      if ((e.target as Element | null)?.closest?.(".pause-card")) return; // Tab/Enter on Resume
      e.preventDefault();
      e.stopPropagation();
    };
    window.addEventListener("keydown", block, true);
    window.addEventListener("keypress", block, true);
    return () => {
      window.removeEventListener("keydown", block, true);
      window.removeEventListener("keypress", block, true);
    };
  }, [paused]);

  async function runTests() {
    if (running) return;
    setRunning(true);
    setRunError(null);
    setTab("tests");
    try {
      await editorRef.current?.saveAll();
      const s = await interviewApi.run();
      const before = snap?.session?.stage;
      setSnap(s);
      if (s.result) setResult(s.result);
      if (before === "bug" && s.session?.stage === "features") setTab("ticket");
      setAppKey((k) => k + 1); // reload the portal so the fix is visible there too
    } catch (e) {
      setRunError((e as Error).message); // shown in the Tests tab until the next run
    } finally {
      setRunning(false);
    }
  }

  if (error && !snap) return <div className="banner error">{error}</div>;
  if (!snap) return <p className="muted">Loading…</p>;
  const { config } = snap;

  if (!session)
    return (
      <InterviewLanding
        snapshot={snap}
        onStarted={(s) => {
          setSnap(s);
          setResult(null);
          setTab("ticket");
          setReloadToken((t) => t + 1);
        }}
      />
    );
  if (session.ended_at)
    return (
      <InterviewReview
        snapshot={snap}
        onGraded={load}
        onRestart={(s) => {
          setSnap(s);
          setResult(null);
          setTab("ticket");
          setReloadToken((t) => t + 1);
        }}
      />
    );

  const elapsed = sessionElapsed(session, now);
  const togglePause = () => {
    const call = paused ? interviewApi.resume() : editorRef.current?.saveAll().then(() => interviewApi.pause());
    void call?.then(setSnap).catch((e: Error) => setError(e.message));
  };
  const left = config.minutes * 60 - elapsed;
  const unlocked = session.stage !== "bug";
  const feature = config.features.find((f) => f.id === session.feature_id) ?? null;
  const lastRun = [...session.events].reverse().find((e) => e.kind === "test_run");
  const [bugPassed, bugTotal] = (lastRun?.bug as [number, number] | undefined) ?? [0, 0];
  const [featPassed, featTotal] = (lastRun?.feature as [number, number] | null | undefined) ?? [0, 0];

  const tabs: { id: Tab; label: string }[] = [
    { id: "ticket", label: unlocked ? "Ticket · Features" : "Ticket" },
    { id: "assistant", label: "AI assistant" },
    { id: "interviewer", label: "Interviewer" },
    { id: "tests", label: "Tests" },
    { id: "app", label: "App" },
    { id: "notes", label: "Narrate" },
  ];

  const chatProps = {
    disabled: false,
    beforeSend: async () => {
      await editorRef.current?.saveAll(); // Claude reads files from disk: give it what you see
      return editorRef.current?.activePath() ?? null;
    },
    afterReply: (changed: string[]) => {
      load(); // refresh the event log
      if (changed.length) {
        editorRef.current?.refresh();
        setAppKey((k) => k + 1);
      }
    },
  };

  return (
    <article className="exercise fullscreen interview" style={{ "--side-w": `${sideWidth}px` } as CSSProperties}>
      <header className="exercise-header interview-header">
        <div className={`interview-timer ${left <= 0 ? "over" : left <= 10 * 60 ? "low" : ""}`} title="Time remaining">
          {left <= 0 ? `+${clock(-left)}` : clock(left)}
        </div>
        {mic.supported && (
          <button
            className={`header-mic ${mic.listening ? "on" : ""}`}
            onClick={mic.toggle}
            title={mic.listening ? "Narrating: click to stop" : "Narrate out loud (speech to text): click to start"}
          >
            {mic.listening ? "● 🎙" : "🎙"}
          </button>
        )}
        <div className="exercise-title">
          <div className="eyebrow">
            {config.sandbox ? "Sandbox (not counted)" : "Mock AI interview"} · {config.minutes} min · {phaseHint(elapsed, config.minutes, session.stage, !!feature)}
          </div>
          <h1>{config.title}</h1>
        </div>
        <ol className="stage-steps">
          <li className={unlocked ? "done" : "current"}>
            1 · Bug {bugTotal > 0 && <span className="muted">{bugPassed}/{bugTotal}</span>}
          </li>
          <li className={!unlocked ? "locked" : session.feature_done ? "done" : "current"}>
            2 · {feature ? feature.title : "Feature"} {feature && featTotal > 0 && <span className="muted">{featPassed}/{featTotal}</span>}
          </li>
        </ol>
        <div className="header-actions">
          <button onClick={togglePause} title="Stop the clock for an interruption. Pauses aren't held against you in the review.">
            ⏸ Pause
          </button>
          <a className="button-link" href="#/ex/py01" title="Back to the trainer. The interview (and its clock) keeps running.">
            ‹ Trainer
          </a>
          <button className="primary" disabled={running} onClick={() => void runTests()}>
            {running ? "Running…" : "▶ Save & run tests"}
          </button>
          <button
            onClick={() => {
              if (window.confirm("End the interview? You'll get the review and grading screen. You can't keep chatting after this.")) {
                void editorRef.current?.saveAll().then(() => interviewApi.end().then(setSnap));
              }
            }}
          >
            End interview
          </button>
        </div>
      </header>
      {error && <div className="banner error">{error}</div>}

      {paused && (
        <div className="pause-overlay" role="dialog" aria-label="Interview paused">
          <div className="pause-card">
            <div className="pause-icon">⏸</div>
            <h2>Interview paused</h2>
            <p className="muted">
              The clock is stopped at <strong>{clock(Math.max(0, config.minutes * 60 - elapsed))}</strong> left. Take care of what you need to; your
              code, chats and notes are saved.
            </p>
            <button className="primary big" autoFocus onClick={togglePause}>
              ▶ Resume
            </button>
            <p className="muted small">Before you resume, take 10 seconds to re-read where you were (the Narrate tab has your last notes).</p>
            {mic.supported && (
              <p className="muted small">
                <strong>Narrating?</strong> The mic turns off while paused. After you resume, click 🎙 in the header to turn it back on.
              </p>
            )}
          </div>
        </div>
      )}

      <CodeEditor
        ref={editorRef}
        exerciseId={config.id}
        initialTabs={[requirementsPath(config.id), `${config.app_root}/README.md`]}
        initialActive={`${config.app_root}/README.md`}
        reloadToken={reloadToken}
        onRun={() => void runTests()}
        tall
      />

      <Splitter
        className="side-splitter"
        label="Interview panel"
        hint="drag to resize"
        onDragStart={() => (dragStart.current = sideWidth)}
        onDrag={(dx) => {
          const width = Math.min(Math.max(dragStart.current - dx, SIDE_MIN), Math.round(window.innerWidth * 0.7));
          setSideWidth(width);
          store(SIDE_KEY, width);
        }}
      />

      <div className="side-panel interview-panel">
        <div className="panel-tabs" role="tablist">
          {tabs.map((t) => (
            <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        {tab === "ticket" && (
          <div className="interview-ticket">
            {unlocked && (
              <section className="card features-card">
                <h2>{feature ? "Your feature request" : "Bug fixed ✓ Pick one feature request"}</h2>
                {!feature && (
                  <p className="muted small">
                    In the real interview you choose from a set of requests as time allows. Tell the interviewer which one you picked and why, then
                    your plan.
                  </p>
                )}
                {config.features
                  .filter((f) => !feature || f.id === feature.id)
                  .map((f) => (
                    <details key={f.id} className="feature" open={!!feature || undefined}>
                      <summary>
                        <strong>{f.title}</strong> <span className="muted">· {f.summary}</span>
                      </summary>
                      <div className="markdown">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{f.spec ?? ""}</ReactMarkdown>
                      </div>
                      {!feature && (
                        <button className="primary" onClick={() => void interviewApi.chooseFeature(f.id).then((s) => { setSnap(s); editorRef.current?.refresh(); })}>
                          Work on this one
                        </button>
                      )}
                      {f.tests.length > 0 && <p className="muted small">Tests: {f.tests.map((t) => t.split("/").pop()).join(", ")}</p>}
                    </details>
                  ))}
              </section>
            )}
            <section className="card markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{config.ticket}</ReactMarkdown>
            </section>
            <section className="card markdown muted-card">
              <h2>About the company & codebase</h2>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{config.company_context}</ReactMarkdown>
            </section>
          </div>
        )}

        {(["assistant", "interviewer"] as Persona[]).map((p) => (
          <div key={p} className="chat-wrap" hidden={tab !== p}>
            {!config.claude_available && <div className="banner error">The `claude` CLI isn't on PATH. Install Claude Code and log in.</div>}
            <InterviewChat persona={p} initial={messagesFromEvents(session.events, p)} {...chatProps} />
          </div>
        ))}

        {tab === "tests" && (
          <div>
            <div className="tests-bar">
              <button className="primary" disabled={running} onClick={() => void runTests()}>
                {running ? "Running…" : "▶ Save & run tests"}
              </button>
              <span className="muted small">Runs the bug's backend + frontend tests{feature ? " and your feature's tests" : ""}. Shortcut: Ctrl/⌘+Enter in the editor.</span>
            </div>
            {runError && <div className="banner error">Test run failed: {runError}</div>}
            <TestResults result={result} running={running} />
            {!result && <p className="muted small pad">Run the tests to see results. Feature tests are added once you pick a feature.</p>}
          </div>
        )}

        {tab === "app" && <AppPreview config={config} reloadKey={appKey} />}

        <div hidden={tab !== "notes"}>
          <Narration events={session.events} onLogged={appendEvent} mic={mic} />
        </div>
      </div>
    </article>
  );
}

function AppPreview({ config, reloadKey }: { config: InterviewSnapshot["config"]; reloadKey: number }) {
  const [key, setKey] = useState(0);
  const [resetting, setResetting] = useState(false);
  return (
    <div className="app-preview">
      <div className="app-preview-bar">
        <span className="muted small">{config.portal_title} (your workspace code, live)</span>
        <button onClick={() => setKey((k) => k + 1)}>↻ Reload</button>
        <button
          disabled={resetting}
          title="Wipe the demo database and reseed it with your current code (the server reloads). Use it after fixing a bug that saved bad data."
          onClick={() => {
            setResetting(true);
            void interviewApi
              .resetData()
              .then(() => new Promise((r) => window.setTimeout(r, 2500))) // let the API reload and reseed
              .then(() => setKey((k) => k + 1))
              .finally(() => setResetting(false));
          }}
        >
          {resetting ? "Reseeding…" : "⟲ Reset demo data"}
        </button>
        <a href={config.portal_path} target="_blank" rel="noreferrer">
          Open in new tab ↗
        </a>
        <a href={`http://127.0.0.1:${config.api_port}/docs`} target="_blank" rel="noreferrer">
          API docs ↗
        </a>
      </div>
      <iframe key={`${reloadKey}-${key}`} title={config.portal_title} src={config.portal_path} />
    </div>
  );
}

interface Mic {
  supported: boolean;
  listening: boolean;
  error: string | null;
  toggle: () => void;
}

/**
 * Speech-to-text narration that lives as long as the interview screen (not just the Narrate tab), so
 * switching panel tabs never stops it. Chrome ends a recognition session after silence or a network
 * blip; we restart it right away, and if that fails (e.g. the tab is in the background) we retry every
 * few seconds and as soon as the tab is visible again.
 */
function useMic(onLogged: (e: InterviewEvent) => void, live: boolean): Mic {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const wantRef = useRef(false);
  const runningRef = useRef(false);
  const loggedRef = useRef(onLogged);
  loggedRef.current = onLogged;

  const begin = useCallback(() => {
    const rec = recRef.current;
    if (!rec || runningRef.current || !wantRef.current) return;
    try {
      rec.start();
      runningRef.current = true;
      setListening(true);
    } catch {
      // "already started" or not allowed right now: the retry timer tries again
    }
  }, []);

  useEffect(() => {
    if (live) return;
    wantRef.current = false; // interview ended: stop listening
    recRef.current?.stop();
    setListening(false);
  }, [live]);

  useEffect(() => {
    const retry = window.setInterval(begin, 3000);
    const onVisible = () => {
      if (!document.hidden) begin();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(retry);
      document.removeEventListener("visibilitychange", onVisible);
      wantRef.current = false;
      recRef.current?.stop();
    };
  }, [begin]);

  const toggle = () => {
    if (!SpeechRecognitionCtor) return;
    if (wantRef.current) {
      wantRef.current = false;
      recRef.current?.stop();
      setListening(false);
      return;
    }
    if (!recRef.current) {
      const rec = new SpeechRecognitionCtor();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = "en-US";
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const text = e.results[i][0].transcript.trim();
          if (e.results[i].isFinal && text) void interviewApi.note(text, "voice").then((ev) => loggedRef.current(ev));
        }
      };
      rec.onerror = (e) => {
        if (e.error === "not-allowed" || e.error === "service-not-allowed") {
          wantRef.current = false;
          setError("Microphone permission denied");
        } else if (e.error !== "no-speech" && e.error !== "aborted") setError(e.error);
      };
      rec.onend = () => {
        runningRef.current = false;
        if (wantRef.current) begin(); // Chrome stops after silence: keep listening
        else setListening(false);
      };
      recRef.current = rec;
    }
    wantRef.current = true;
    setError(null);
    begin();
  };

  return { supported: !!SpeechRecognitionCtor, listening, error, toggle };
}

function Narration({ events, onLogged, mic }: { events: InterviewEvent[]; onLogged: (e: InterviewEvent) => void; mic: Mic }) {
  const [draft, setDraft] = useState("");
  const notes = events.filter((e) => e.kind === "note");

  const log = useCallback(
    (text: string, source: "typed" | "voice") => {
      if (text.trim()) void interviewApi.note(text, source).then(onLogged);
    },
    [onLogged],
  );

  return (
    <div className="narration">
      <p className="muted small">
        Interviewers grade what they can follow. Say (or type) your hypotheses, decisions and trade-offs as you go. Each note is time-stamped and
        goes into the review.
      </p>
      {mic.supported && (
        <button className={`mic ${mic.listening ? "on" : ""}`} onClick={mic.toggle}>
          {mic.listening ? "● Listening… (click to stop)" : "🎙 Narrate out loud (speech to text)"}
        </button>
      )}
      {mic.error && <div className="banner error">{mic.error}</div>}
      <p className="muted small">
        The mic keeps listening while you use the other tabs, and while this browser tab is in the background (it reconnects if Chrome drops it).
        The 🎙 button in the header shows whether it's on.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          log(draft, "typed");
          setDraft("");
        }}
      >
        <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="e.g. Hypothesis: the period is computed in UTC…" />
      </form>
      <ol className="timeline">
        {[...notes].reverse().map((n, i) => (
          <li key={i}>
            <span className="stamp">{clock(n.elapsed)}</span> {n.source === "voice" ? "🎙 " : ""}
            {String(n.text)}
          </li>
        ))}
      </ol>
    </div>
  );
}

function InterviewLanding({ snapshot, onStarted }: { snapshot: InterviewSnapshot; onStarted: (s: InterviewSnapshot) => void }) {
  const { config, scenarios, active } = snapshot;
  const [resetCode, setResetCode] = useState(true);
  const [busy, setBusy] = useState(false);
  const autoStarted = useRef(false);
  useEffect(() => {
    // The sandbox is a demo: opening it goes straight into the interview screen.
    if (!config.sandbox || autoStarted.current) return;
    autoStarted.current = true;
    setBusy(true);
    interviewApi
      .start(config.id, true)
      .then(onStarted)
      .finally(() => setBusy(false));
  }, [config.sandbox, config.id, onStarted]);
  if (config.sandbox) return <p className="muted pad">Opening the sandbox…</p>;
  const other = active && active.scenario !== config.id ? scenarios.find((s) => s.id === active.scenario) : null;
  return (
    <article className="exercise interview-landing">
      <header className="exercise-header">
        <div className="exercise-title">
          <div className="eyebrow">
            {config.generated ? "Generated scenario" : `Mock AI interview #${config.order}`} · {config.minutes} min
          </div>
          <h1>{config.title}</h1>
        </div>
      </header>
      <nav className="scenario-picker">
        {scenarios.map((s) => (
          <a key={s.id} href={`#/ex/${s.id}`} className={s.id === config.id ? "active" : ""}>
            <span className="muted small">{s.sandbox ? "demo" : s.order >= 10 ? "✨" : `#${s.order}`}</span> {s.title}
          </a>
        ))}
      </nav>
      {other && active && (
        <div className="banner">
          Interview #{other.order} ({other.title}) is still running ({clock(active.elapsed)} in).{" "}
          <a href={`#/ex/${other.id}`}>Go back to it</a>, or start this one, which ends it.
        </div>
      )}
      <section className="card markdown">
        <h2>What this simulates</h2>
        <p>
          The Acme Health "AI coding interview": a browser IDE on an existing full-stack codebase (Python, FastAPI, TypeScript, React) with an AI
          assistant built in. You first <strong>debug a user-reported error</strong>; once its tests pass, <strong>feature requests unlock</strong>{" "}
          and you pick one as time allows. Each numbered interview is a different codebase and bug in the same provider-payments world, so you can
          measure how you improve from one attempt to the next.
        </p>
        <ul>
          <li>
            <strong>AI assistant</strong> tab: Claude (via your local Claude Code login) can read, search and edit the app's code and run the
            backend tests. Use it the way you would at work.
          </li>
          <li>
            <strong>Interviewer</strong> tab: a Claude-played interviewer who knows the domain. Ask clarifying questions; it won't give you the
            answer.
          </li>
          <li>
            <strong>Narrate</strong> tab: think out loud (speech to text in Chrome) or type notes. Everything (prompts, replies, test runs, notes)
            is logged with timestamps, and at the end Claude grades the session against the interview's criteria.
          </li>
          <li>
            <strong>App</strong> tab: the {config.portal_title.toLowerCase()} running your workspace code (needs <code>npm run dev</code>, which
            starts its API on port {config.api_port}).
          </li>
        </ul>
        <p className="muted small">
          Tips from the brief: think out loud · use the AI like you normally would · ask the interviewer about the domain · you're graded on solving
          the problem and building for real users, not on prompting style.
        </p>
        {!config.claude_available && <div className="banner error">The `claude` CLI isn't on PATH, so the AI tabs won't work.</div>}
        <label className="toggle">
          <input type="checkbox" checked={resetCode} onChange={(e) => setResetCode(e.target.checked)} />
          Start from a fresh copy of the codebase (recommended)
        </label>
        <p>
          <button
            className="primary big"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              interviewApi
                .start(config.id, resetCode)
                .then(onStarted)
                .finally(() => setBusy(false));
            }}
          >
            {busy ? "Starting…" : `▶ Start ${config.generated ? "the interview" : `interview #${config.order}`} (${config.minutes} min)`}
          </button>
        </p>
        <p className="muted small">The clock starts immediately. It doesn't pause; when it runs out you can keep going and it shows overtime.</p>
      </section>
      <InterviewAttempts />
      <GenerateScenario />
      {config.generated && (
        <p className="muted small">
          This scenario was generated.{" "}
          <button
            onClick={() => {
              if (window.confirm(`Delete "${config.title}"? Its files are removed; your past session logs stay.`))
                void generateApi
                  .deleteScenario(config.id)
                  .then(() => {
                    window.location.hash = "#/";
                    window.location.reload();
                  })
                  .catch((e: Error) => window.alert(e.message));
            }}
          >
            Delete this generated scenario
          </button>
        </p>
      )}
    </article>
  );
}
