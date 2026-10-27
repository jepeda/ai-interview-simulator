import { useEffect, useRef, useState, type CSSProperties } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  requirementsPath,
  trainerApi,
  vscodeLink,
  type EditorId,
  type ExerciseDetail,
  type ExerciseSummary,
  type Meta,
} from "../api";
import { CodeEditor, type CodeEditorHandle } from "../editor/CodeEditor";
import { readNumber, Splitter, store } from "../editor/Splitter";
import { StatusDot } from "./ExerciseList";
import { QuickRef } from "./QuickRef";
import { TestResults } from "./TestResults";

interface Props {
  id: string;
  meta: Meta | null;
  exercises: ExerciseSummary[];
  onChanged: () => void;
}

const EXTERNAL_EDITOR_KEY = "trainer.externalEditor";
const FULLSCREEN_KEY = "trainer.fullscreen";
const SIDE_PANEL_KEY = "trainer.sidePanel";
const SIDE_WIDTH_KEY = "trainer.sideWidth";
const SIDE_MIN = 280;
const SIDE_COLLAPSE_BELOW = 160; // dragging narrower than this hides the panel
const PANEL_TAB_KEY = "trainer.panelTab";
type PanelTab = "results" | "docs";

function readSetting(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeSetting(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

/**
 * Every exercise opens REQUIREMENTS.md first. Projects add their README (the tree has everything
 * else); small exercises add their files + tests.
 */
function initialTabs(ex: ExerciseDetail): string[] {
  const requirements = requirementsPath(ex.id);
  if (ex.track === "project") {
    const readme = ex.files.find((f) => f.path.endsWith("/README.md"));
    return [requirements, readme?.path ?? ex.files[0].path];
  }
  return [requirements, ...ex.files.map((f) => f.path), ...ex.tests.map((t) => t.path)];
}

export function ExerciseView({ id, meta, exercises, onChanged }: Props) {
  const [ex, setEx] = useState<ExerciseDetail | null>(null);
  const [busy, setBusy] = useState<null | "run" | "hint" | "reset" | "complete">(null);
  const [notice, setNotice] = useState<{ kind: "info" | "error"; text: string; link?: string } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [externalEditor, setExternalEditor] = useState(() => readSetting(EXTERNAL_EDITOR_KEY, "webstorm") as EditorId);
  // Full screen is remembered, so the next exercise opens the same way.
  const [fullscreen, setFullscreenState] = useState(() => readSetting(FULLSCREEN_KEY, "0") === "1");
  const [sidePanel, setSidePanelState] = useState(() => readSetting(SIDE_PANEL_KEY, "1") === "1");
  const [sideWidth, setSideWidth] = useState(() => readNumber(SIDE_WIDTH_KEY, Math.round(window.innerWidth * 0.34)));
  const sideDragStart = useRef(sideWidth);
  const [panelTab, setPanelTabState] = useState(() => readSetting(PANEL_TAB_KEY, "results") as PanelTab);
  const editorRef = useRef<CodeEditorHandle>(null);
  const runningRef = useRef(false); // synchronous guard: one keypress = one run

  const setFullscreen = (on: boolean) => {
    setFullscreenState(on);
    writeSetting(FULLSCREEN_KEY, on ? "1" : "0");
  };
  const setPanelTab = (tab: PanelTab) => {
    setPanelTabState(tab);
    writeSetting(PANEL_TAB_KEY, tab);
  };
  const setSidePanel = (on: boolean) => {
    setSidePanelState(on);
    writeSetting(SIDE_PANEL_KEY, on ? "1" : "0");
  };

  // Full screen covers the page: stop it scrolling underneath, and let Esc (outside the editor) exit.
  useEffect(() => {
    if (!fullscreen) return;
    document.body.classList.add("no-scroll");
    const onKey = (e: KeyboardEvent) => {
      const inEditor = (e.target as Element | null)?.closest?.(".monaco-editor, input, select, textarea");
      if (e.key === "Escape" && !inEditor) setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.classList.remove("no-scroll");
      window.removeEventListener("keydown", onKey);
    };
  }, [fullscreen]);

  useEffect(() => {
    trainerApi
      .get(id)
      .then(setEx)
      .catch((e: Error) => setNotice({ kind: "error", text: e.message }));
  }, [id]);

  async function act(kind: NonNullable<typeof busy>, fn: () => Promise<ExerciseDetail>) {
    setBusy(kind);
    setNotice(null);
    try {
      setEx(await fn());
      onChanged();
    } catch (e) {
      setNotice({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(null);
    }
  }

  async function runTests() {
    if (runningRef.current) return;
    runningRef.current = true;
    try {
      await editorRef.current?.saveAll();
      setPanelTab("results");
      await act("run", () => trainerApi.run(id));
    } catch (e) {
      setNotice({ kind: "error", text: `Couldn't save before running: ${(e as Error).message}` });
    } finally {
      runningRef.current = false;
    }
  }

  async function openExternally(path: string, absPath: string) {
    try {
      await editorRef.current?.saveAll();
      const res = await trainerApi.open(path, externalEditor);
      const fallback = externalEditor === "vscode" ? vscodeLink(absPath) : undefined;
      setNotice(res.opened ? { kind: "info", text: res.message } : { kind: "error", text: res.message, link: fallback });
    } catch (e) {
      setNotice({ kind: "error", text: (e as Error).message });
    }
  }

  // Ctrl/Cmd + Enter anywhere on the page saves and runs the tests (the editor handles its own).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        void runTests();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (!ex) {
    return notice ? <div className="banner error">{notice.text}</div> : <p className="muted">Loading…</p>;
  }

  const completed = ex.status === "completed";
  const hintsLeft = ex.hints_total - ex.hints.length;
  const editors = meta?.editors ?? [];
  const index = exercises.findIndex((e) => e.id === ex.id);
  const goTo = (target: ExerciseSummary | undefined) => {
    if (target) window.location.hash = `#/ex/${target.id}`;
  };

  return (
    <article
      className={`exercise ${fullscreen ? "fullscreen" : ""} ${fullscreen && !sidePanel ? "no-side" : ""}`}
      style={fullscreen ? ({ "--side-w": `${sideWidth}px` } as CSSProperties) : undefined}
    >
      <header className="exercise-header">
        {fullscreen && (
          <nav className="fs-nav" aria-label="Exercises">
            <button disabled={index <= 0} title="Previous exercise" onClick={() => goTo(exercises[index - 1])}>
              ‹
            </button>
            <select value={ex.id} onChange={(e) => goTo(exercises.find((x) => x.id === e.target.value))}>
              {exercises.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.status === "completed" ? "✓ " : ""}
                  {x.id} · {x.title}
                </option>
              ))}
            </select>
            <button
              disabled={index < 0 || index >= exercises.length - 1}
              title="Next exercise"
              onClick={() => goTo(exercises[index + 1])}
            >
              ›
            </button>
          </nav>
        )}
        <div className="exercise-title">
          <div className="eyebrow">
            <StatusDot status={ex.status} /> {ex.id} · {{ syntax: "Syntax drill", debugging: "Debugging challenge", project: "Interview project", interview: "Mock interview" }[ex.track]} · ~
            {ex.minutes} min
            {ex.times_completed > 0 && <span className="muted"> · completed {ex.times_completed}×</span>}
          </div>
          <h1>{ex.title}</h1>
          <div className="chips">
            {ex.topics.map((t) => (
              <span key={t} className="chip">
                {t}
              </span>
            ))}
          </div>
        </div>
        <div className="header-actions">
          {fullscreen && ex.last_result && (
            <span className={`fs-score ${ex.last_result.ok ? "pass" : "fail"}`}>
              {ex.last_result.passed}/{ex.last_result.total} passing
            </span>
          )}
          <button className="primary" disabled={busy !== null} onClick={() => void runTests()}>
            {busy === "run" ? "Running…" : "▶ Save & run tests"}
          </button>
          <span className="kbd-hint">Ctrl/⌘ + Enter</span>
          {fullscreen && (
            <button className={sidePanel ? "on" : ""} title="Tests, hints and quick reference" onClick={() => setSidePanel(!sidePanel)}>
              {sidePanel ? "Hide panel" : "Show panel"}
            </button>
          )}
          <button
            title={fullscreen ? "Exit full screen (Esc)" : "Full-screen IDE"}
            onClick={() => setFullscreen(!fullscreen)}
          >
            {fullscreen ? "Exit full screen" : "⛶ Full screen"}
          </button>
        </div>
      </header>

      {notice && (
        <div className={`banner ${notice.kind}`}>
          {notice.text}
          {notice.link && (
            <>
              {" "}
              <a href={notice.link}>Open via vscode:// link</a>
            </>
          )}
        </div>
      )}

      <section className="card markdown requirements-card">
        <h2>Requirements</h2>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{ex.requirements}</ReactMarkdown>
      </section>

      <CodeEditor
        ref={editorRef}
        exerciseId={ex.id}
        initialTabs={initialTabs(ex)}
        initialActive={fullscreen || ex.track === "project" ? requirementsPath(ex.id) : ex.files[0].path}
        reloadToken={reloadToken}
        onRun={() => void runTests()}
        tall={ex.track === "project"}
      />

      <div className="external-row">
        <span className="muted small">Prefer your IDE? Edits sync both ways (the editor reloads when you switch back).</span>
        <select
          value={externalEditor}
          onChange={(e) => {
            const value = e.target.value as EditorId;
            setExternalEditor(value);
            writeSetting(EXTERNAL_EDITOR_KEY, value);
          }}
        >
          {editors.map((ed) => (
            <option key={ed.id} value={ed.id}>
              {ed.label}
              {ed.available ? "" : " (not found)"}
            </option>
          ))}
        </select>
        <button onClick={() => void openExternally(ex.files[0].path, ex.files[0].abs_path)}>Open file</button>
      </div>

      {fullscreen && sidePanel && (
        <Splitter
          className="side-splitter"
          label="Side panel"
          onDragStart={() => (sideDragStart.current = sideWidth)}
          onDrag={(dx) => {
            const width = sideDragStart.current - dx; // dragging left widens the panel
            if (width < SIDE_COLLAPSE_BELOW) {
              setSidePanel(false);
              return;
            }
            const clamped = Math.min(Math.max(width, SIDE_MIN), Math.round(window.innerWidth * 0.65));
            setSideWidth(clamped);
            store(SIDE_WIDTH_KEY, clamped);
          }}
          onDoubleClick={() => setSidePanel(false)}
        />
      )}
      {fullscreen && !sidePanel && (
        <button className="rail rail-right" title="Show tests, hints and quick ref" onClick={() => setSidePanel(true)}>
          <span>‹</span>
          <span className="rail-label">Tests · Hints · Quick ref</span>
        </button>
      )}
      <div className="side-panel">
        <div className="panel-tabs" role="tablist">
          <button role="tab" aria-selected={panelTab === "results"} className={panelTab === "results" ? "active" : ""} onClick={() => setPanelTab("results")}>
            Tests & hints
          </button>
          <button role="tab" aria-selected={panelTab === "docs"} className={panelTab === "docs" ? "active" : ""} onClick={() => setPanelTab("docs")}>
            Quick ref
          </button>
        </div>
        {panelTab === "docs" ? (
          <QuickRef relevant={ex.quickref} />
        ) : (
          <>
            <TestResults result={ex.last_result} running={busy === "run"} />

            <section className="card">
              <h2>
                Hints <span className="muted small">({ex.hints.length}/{ex.hints_total} revealed)</span>
              </h2>
              {ex.hints.length === 0 && <p className="muted">Try it first. Hints are revealed one at a time and never give the full answer.</p>}
              <ol className="hints">
                {ex.hints.map((h, i) => (
                  <li key={i} className="markdown">
                    <ReactMarkdown>{h}</ReactMarkdown>
                  </li>
                ))}
              </ol>
              {hintsLeft > 0 ? (
                <button disabled={busy !== null} onClick={() => act("hint", () => trainerApi.hint(ex.id))}>
                  {busy === "hint" ? "…" : `Show hint ${ex.hints.length + 1} of ${ex.hints_total}`}
                </button>
              ) : (
                <p className="muted small">
                  No more hints. Reference solutions are kept separately in <code>backend/solutions/</code> if you're truly stuck.
                </p>
              )}
            </section>

            <section className="card actions-row">
              <button
                disabled={busy !== null}
                onClick={() => act("complete", () => trainerApi.complete(ex.id, !completed))}
              >
                {completed ? "Mark as not complete" : "Mark complete manually"}
              </button>
              {!confirmReset ? (
                <button className="danger-outline" disabled={busy !== null} onClick={() => setConfirmReset(true)}>
                  Reset exercise…
                </button>
              ) : (
                <span className="confirm">
                  Restore the starter file(s)? <strong>Your edits will be lost.</strong>
                  <button
                    className="danger"
                    onClick={() => {
                      setConfirmReset(false);
                      void act("reset", () => trainerApi.reset(ex.id)).then(() => setReloadToken((t) => t + 1));
                    }}
                  >
                    Yes, reset
                  </button>
                  <button className="ghost" onClick={() => setConfirmReset(false)}>
                    Cancel
                  </button>
                </span>
              )}
              <span className="muted small">
                {ex.attempts} run{ex.attempts === 1 ? "" : "s"} this attempt
              </span>
            </section>
          </>
        )}
      </div>
    </article>
  );
}
