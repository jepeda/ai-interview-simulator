import Editor, { type OnMount } from "@monaco-editor/react";
import { useCallback, useEffect, useImperativeHandle, useRef, useState, type Ref } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { editorApi, type TreeFile } from "../api";
import { FileTree } from "./FileTree";
import { readNumber, Splitter, store } from "./Splitter";
import {
  ensureClinicTypes,
  intellisenseOptions,
  isIntellisenseOn,
  lintModel,
  monaco,
  setFileOpener,
  setIntellisenseOn,
  uriFor,
} from "./monacoSetup";

export interface CodeEditorHandle {
  /** Write every modified file to disk. Resolves once all saves finished. */
  saveAll: () => Promise<void>;
  /** Re-read the tree and every open file you haven't modified (e.g. after the AI assistant edited files). */
  refresh: () => void;
  /** The file in the focused pane. */
  activePath: () => string | null;
}

interface Props {
  exerciseId: string;
  initialTabs: string[]; // files opened as tabs when the exercise loads
  initialActive?: string; // tab shown first (default: the first tab)
  reloadToken: number; // bump to re-read everything from disk (e.g. after reset)
  onRun: () => void; // Ctrl/Cmd+Enter inside the editor
  tall?: boolean;
  ref?: Ref<CodeEditorHandle>;
}

interface OpenFile {
  path: string;
  content: string; // editor text as React last saw it
  saved: string; // text on disk as of the last load/save
  language: string;
  readOnly: boolean;
}

/** One editor group. With a split there are two, side by side, each with its own tabs. */
interface Pane {
  tabs: string[];
  active: string;
}

const TREE_SHOWN_KEY = "trainer.treeShown";
const TREE_WIDTH_KEY = "trainer.treeWidth";
const TREE_MIN = 150;
const TREE_COLLAPSE_BELOW = 90; // dragging narrower than this hides the tree
const SPLIT_KEY = "trainer.split";
const SPLIT_RATIO_KEY = "trainer.splitRatio";
const TAB_DRAG_TYPE = "application/x-trainer-tab";

const prefersDark = () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
const baseName = (p: string) => p.split("/").pop() ?? p;

/**
 * The text actually in the editor. Read from Monaco's model rather than React state: a save fired by
 * a keystroke (Ctrl+S / Ctrl+Enter) can run before React re-renders with the last characters typed.
 */
function liveContent(f: OpenFile): string {
  const model = monaco.editor.getModel(monaco.Uri.parse(uriFor(f.path)));
  return model && !model.isDisposed() ? model.getValue() : f.content;
}

/** Tab labels: the file name, plus its folder when two open tabs share a name (e.g. __init__.py). */
function tabLabels(paths: string[]): Record<string, string> {
  const counts = new Map<string, number>();
  for (const p of paths) counts.set(baseName(p), (counts.get(baseName(p)) ?? 0) + 1);
  return Object.fromEntries(
    paths.map((p) => [p, (counts.get(baseName(p)) ?? 0) > 1 ? p.split("/").slice(-2).join("/") : baseName(p)]),
  );
}

/** The pane a split opens: the same tabs, showing the tab after the current one (e.g. code -> tests). */
function splitFrom(pane: Pane): Pane {
  const i = pane.tabs.indexOf(pane.active);
  return { tabs: pane.tabs, active: pane.tabs[i + 1] ?? pane.tabs[i - 1] ?? pane.active };
}

function initialPanes(tabs: string[], active: string): Pane[] {
  const first = { tabs, active };
  try {
    if (localStorage.getItem(SPLIT_KEY) === "true" && tabs.length > 1) return [first, splitFrom(first)];
  } catch {
    /* ignore */
  }
  return [first];
}

export function CodeEditor({ exerciseId, initialTabs, initialActive, reloadToken, onRun, tall, ref }: Props) {
  const [tree, setTree] = useState<TreeFile[]>([]);
  const [showTree, setShowTreeState] = useState(() => {
    try {
      return localStorage.getItem(TREE_SHOWN_KEY) !== "false";
    } catch {
      return true;
    }
  });
  const [treeWidth, setTreeWidth] = useState(() => readNumber(TREE_WIDTH_KEY, 240));
  const dragStartWidth = useRef(treeWidth);
  const [open, setOpen] = useState<Record<string, OpenFile>>({});
  const [panes, setPanes] = useState<Pane[]>(() => initialPanes(initialTabs, initialActive ?? initialTabs[0]));
  const [focused, setFocused] = useState(0); // pane that the file tree, F12 and the status bar act on
  const [splitRatio, setSplitRatio] = useState(() => Math.min(readNumber(SPLIT_RATIO_KEY, 0.5), 0.8));
  const dragStartRatio = useRef(splitRatio);
  const panesEl = useRef<HTMLDivElement>(null);
  const [mdSource, setMdSource] = useState<Set<string>>(new Set()); // markdown tabs showing source, not preview
  const [intellisense, setIntellisense] = useState(isIntellisenseOn);
  const [status, setStatus] = useState<string>("");
  const [dark, setDark] = useState(prefersDark);
  const editorRefs = useRef<(monaco.editor.IStandaloneCodeEditor | null)[]>([]);

  // Refs so Monaco actions (registered once) and async callbacks always see current state.
  const openRef = useRef(open);
  openRef.current = open;
  const panesRef = useRef(panes);
  panesRef.current = panes;
  const focusedRef = useRef(focused);
  focusedRef.current = Math.min(focused, panes.length - 1);
  const onRunRef = useRef(onRun);
  onRunRef.current = onRun;

  const setShowTree = useCallback((shown: boolean) => {
    setShowTreeState(shown);
    store(TREE_SHOWN_KEY, shown);
  }, []);
  const showTreeRef = useRef(showTree);
  showTreeRef.current = showTree;
  const toggleTree = useCallback(() => setShowTree(!showTreeRef.current), [setShowTree]);

  const updatePane = useCallback((index: number, change: (p: Pane) => Pane) => {
    setPanes((ps) => ps.map((p, i) => (i === index ? change(p) : p)));
  }, []);

  /** Split into two panes, or merge back into one (keeping every tab that was open). */
  const toggleSplit = useCallback((keepIndex?: number) => {
    const ps = panesRef.current;
    if (ps.length > 1) {
      const keep = ps[keepIndex ?? focusedRef.current]; // its file stays on screen
      const tabs = [...new Set([...ps[0].tabs, ...ps[1].tabs])];
      setPanes([{ tabs, active: keep.active }]);
      setFocused(0);
      editorRefs.current.length = 1;
      store(SPLIT_KEY, false);
    } else {
      setPanes([ps[0], splitFrom(ps[0])]);
      setFocused(1);
      store(SPLIT_KEY, true);
    }
  }, []);

  // Ctrl/Cmd+B toggles the file tree, Ctrl/Cmd+\ splits the editor (like VS Code).
  // Inside Monaco the editor actions below handle them.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const inEditor = (e.target as Element | null)?.closest?.(".monaco-editor");
      if (!(e.ctrlKey || e.metaKey) || e.shiftKey || e.altKey || inEditor) return;
      if (e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggleTree();
      } else if (e.key === "\\") {
        e.preventDefault();
        toggleSplit();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggleTree, toggleSplit]);

  const loadTree = useCallback(() => {
    editorApi
      .tree(exerciseId)
      .then((t) => setTree(t.files))
      .catch(() => setStatus("Could not load the file tree"));
  }, [exerciseId]);

  /** (Re)load files from disk. onlyUnmodified: never clobber text you haven't saved. */
  const loadFiles = useCallback(async (paths: string[], onlyUnmodified: boolean) => {
    const results = await Promise.allSettled(paths.map((p) => editorApi.read(p)));
    setOpen((prev) => {
      const next = { ...prev };
      for (const r of results) {
        if (r.status !== "fulfilled") continue;
        const f = r.value;
        const existing = prev[f.path];
        const dirty = existing && liveContent(existing) !== existing.saved;
        if (onlyUnmodified && dirty) continue;
        if (existing && existing.saved === f.content && !dirty) continue;
        next[f.path] = { path: f.path, content: f.content, saved: f.content, language: f.language, readOnly: f.read_only };
      }
      return next;
    });
    if (results.some((r) => r.status === "rejected")) setStatus("Some files could not be loaded");
    return results.flatMap((r) => (r.status === "fulfilled" ? [r.value.path] : []));
  }, []);

  /** Move the cursor once the pane's editor is actually showing `path` (model switches happen asynchronously). */
  const revealWhenShown = useCallback((pane: number, path: string, line: number, column: number) => {
    const target = monaco.Uri.parse(uriFor(path)).toString();
    const deadline = performance.now() + 2000;
    const attempt = () => {
      const editor = editorRefs.current[pane];
      if (editor && editor.getModel()?.uri.toString() === target) {
        editor.setPosition({ lineNumber: line, column });
        editor.revealLineInCenter(line);
        editor.focus();
      } else if (performance.now() < deadline) {
        window.setTimeout(attempt, 16); // not requestAnimationFrame: it's paused in background tabs
      }
    };
    window.setTimeout(attempt, 0);
  }, []);

  /** Open `path` as the active tab of the focused pane. */
  const openFile = useCallback(
    async (path: string, reveal?: { line: number; column: number }) => {
      const pane = focusedRef.current;
      // Load BEFORE switching: switching to an unloaded file would unmount (and recreate) Monaco.
      if (!openRef.current[path] && !(await loadFiles([path], false)).includes(path)) {
        setStatus(`Could not open ${path}`);
        return;
      }
      updatePane(pane, (p) => ({ tabs: p.tabs.includes(path) ? p.tabs : [...p.tabs, path], active: path }));
      if (reveal) revealWhenShown(pane, path, reveal.line, reveal.column);
    },
    [loadFiles, revealWhenShown, updatePane],
  );

  // Initial load + after reset.
  useEffect(() => {
    loadTree();
    void loadFiles([...new Set(panesRef.current.flatMap((p) => p.tabs))], false);
  }, [loadTree, loadFiles, reloadToken]);

  // Coming back from WebStorm/VS Code: pick up their edits and any new files.
  useEffect(() => {
    const onFocus = () => {
      loadTree();
      void loadFiles(Object.keys(openRef.current), true);
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [loadTree, loadFiles]);

  // F12 / Cmd+click into another file opens it in a tab.
  useEffect(() => {
    setFileOpener((path, line, column) => void openFile(path, { line, column }));
    return () => setFileOpener(null);
  }, [openFile]);

  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    const onChange = () => setDark(mq.matches);
    mq?.addEventListener("change", onChange);
    return () => mq?.removeEventListener("change", onChange);
  }, []);

  const saveFiles = useCallback(async (files: OpenFile[]) => {
    const dirty = files
      .filter((f) => !f.readOnly)
      .map((f) => ({ ...f, content: liveContent(f) }))
      .filter((f) => f.content !== f.saved);
    if (dirty.length === 0) return;
    await Promise.all(dirty.map((f) => editorApi.save(f.path, f.content)));
    setOpen((prev) => {
      const next = { ...prev };
      for (const f of dirty) next[f.path] = { ...next[f.path], saved: f.content };
      return next;
    });
    setStatus(`Saved ${dirty.map((f) => baseName(f.path)).join(", ")} · ${new Date().toLocaleTimeString()}`);
  }, []);

  const saveAll = useCallback(() => saveFiles(Object.values(openRef.current)), [saveFiles]);

  useImperativeHandle(
    ref,
    () => ({
      saveAll,
      refresh: () => {
        loadTree();
        void loadFiles(Object.keys(openRef.current), true);
      },
      activePath: () => panesRef.current[focusedRef.current]?.active ?? null,
    }),
    [saveAll, loadTree, loadFiles],
  );

  // Save unsaved work when leaving the exercise; warn when closing the browser tab.
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (Object.values(openRef.current).some((f) => !f.readOnly && liveContent(f) !== f.saved)) e.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("beforeunload", warn);
      for (const f of Object.values(openRef.current)) {
        const content = liveContent(f);
        if (!f.readOnly && content !== f.saved) void editorApi.save(f.path, content);
      }
    };
  }, []);

  /** Close a pane's tab. Closing the last tab of a split pane closes the split. */
  function closeTab(index: number, path: string) {
    const f = openRef.current[path];
    if (f) void saveFiles([f]); // closing never loses work
    const pane = panes[index];
    const remaining = pane.tabs.filter((t) => t !== path);
    if (remaining.length === 0) {
      setPanes(panes.filter((_, i) => i !== index));
      setFocused(0);
      editorRefs.current.length = 1;
      store(SPLIT_KEY, false);
      return;
    }
    const active = pane.active === path ? remaining[Math.max(0, pane.tabs.indexOf(path) - 1)] : pane.active;
    updatePane(index, () => ({ tabs: remaining, active }));
  }

  /** Drop a tab dragged from the other pane: move it here (closing that pane if it was its last tab). */
  function dropTab(index: number, e: React.DragEvent) {
    const data = e.dataTransfer.getData(TAB_DRAG_TYPE);
    if (!data) return;
    e.preventDefault();
    const { from, path } = JSON.parse(data) as { from: number; path: string };
    if (from === index) return;
    const source = panes[from].tabs.filter((t) => t !== path);
    const target = panes[index];
    const moved: Pane = { tabs: target.tabs.includes(path) ? target.tabs : [...target.tabs, path], active: path };
    if (source.length === 0) {
      setPanes([moved]);
      editorRefs.current.length = 1;
      store(SPLIT_KEY, false);
      setFocused(0);
    } else {
      const sourceActive = panes[from].active === path ? source[0] : panes[from].active;
      setPanes(panes.map((p, i) => (i === index ? moved : i === from ? { tabs: source, active: sourceActive } : p)));
      setFocused(index);
    }
  }

  const focusedPane = Math.min(focused, panes.length - 1);
  const current = open[panes[focusedPane].active];
  const visible = panes.map((p) => open[p.active]).filter((f): f is OpenFile => !!f);

  // Lint the visible Python files shortly after typing stops.
  const lintKey = visible.map((f) => (f.language === "python" ? `${f.path}\0${f.content}` : "")).join("\0");
  useEffect(() => {
    const timer = window.setTimeout(() => {
      for (const f of visible) {
        if (f.language !== "python") continue;
        const model = monaco.editor.getModel(monaco.Uri.parse(uriFor(f.path)));
        if (model) void lintModel(model);
      }
    }, 450);
    return () => window.clearTimeout(timer);
  }, [lintKey]);

  const anyTypescript = visible.some((f) => f.language === "typescript");
  useEffect(() => {
    if (anyTypescript) void ensureClinicTypes();
  }, [anyTypescript]);

  useEffect(() => {
    for (const editor of editorRefs.current) editor?.updateOptions(intellisenseOptions(intellisense));
  }, [intellisense]);

  const onMountFor =
    (index: number): OnMount =>
    (editor) => {
      editorRefs.current[index] = editor;
      editor.onDidFocusEditorWidget(() => setFocused(index));
      // Record edits under the model that actually changed, not a render's `file`: Monaco also fires
      // change events while a pane switches files, and a stale closure would file one file's text
      // under another file's path (corrupting it on the next save).
      editor.onDidChangeModelContent(() => {
        const model = editor.getModel();
        if (!model) return;
        const path = model.uri.path.replace(/^\//, "");
        const value = model.getValue();
        setOpen((prev) => {
          const f = prev[path];
          return !f || f.readOnly || f.content === value ? prev : { ...prev, [path]: { ...f, content: value } };
        });
      });
      // addAction, not addCommand: addCommand keybindings are global in Monaco, so a disposed editor's
      // handler (from a previous exercise) would keep firing with stale state.
      editor.addAction({
        id: "trainer.save",
        label: "Save",
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
        run: () => void saveAll(),
      });
      editor.addAction({
        id: "trainer.run",
        label: "Save & run tests",
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
        run: () => onRunRef.current(),
      });
      editor.addAction({
        id: "trainer.toggleFiles",
        label: "Toggle file tree",
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB],
        run: () => toggleTree(),
      });
      editor.addAction({
        id: "trainer.toggleSplit",
        label: "Split editor",
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Backslash],
        run: () => toggleSplit(),
      });
    };

  const dirtyPaths = new Set(Object.values(open).filter((f) => !f.readOnly && f.content !== f.saved).map((f) => f.path));
  const split = panes.length > 1;

  function renderPane(pane: Pane, index: number) {
    const file = open[pane.active];
    const preview = file?.language === "markdown" && !mdSource.has(file.path);
    const labels = tabLabels(pane.tabs);
    const last = index === panes.length - 1;
    return (
      <div
        key={index}
        className={`editor-pane ${split && index === focusedPane ? "focused" : ""}`}
        style={split ? { flex: `${index === 0 ? splitRatio : 1 - splitRatio} 1 0` } : undefined}
        onMouseDown={() => setFocused(index)}
      >
        <div
          className="editor-toolbar"
          onDragOver={(e) => {
            if (split && e.dataTransfer.types.includes(TAB_DRAG_TYPE)) e.preventDefault();
          }}
          onDrop={(e) => dropTab(index, e)}
        >
          {index === 0 && (
            <button
              className={`tree-toggle ${showTree ? "on" : ""}`}
              title={`${showTree ? "Hide" : "Show"} files (Ctrl/⌘+B)`}
              onClick={toggleTree}
            >
              ☰ Files
            </button>
          )}
          <div className="editor-tabs" role="tablist">
            {pane.tabs.map((p) => {
              const f = open[p];
              const closable = pane.tabs.length > 1 || split;
              return (
                <div
                  key={p}
                  role="tab"
                  aria-selected={p === pane.active}
                  className={`editor-tab ${p === pane.active ? "active" : ""} ${f?.readOnly ? "test" : ""}`}
                  title={split ? `${p}\nDrag to the other side to move it` : p}
                  draggable={split}
                  onDragStart={(e) => e.dataTransfer.setData(TAB_DRAG_TYPE, JSON.stringify({ from: index, path: p }))}
                >
                  <button className="tab-label" onClick={() => updatePane(index, (x) => ({ ...x, active: p }))}>
                    {f?.readOnly ? "🔒 " : ""}
                    {labels[p]}
                  </button>
                  {dirtyPaths.has(p) && <span className="dirty-dot" aria-label="unsaved" />}
                  {closable && (
                    <button className="tab-close" aria-label={`Close ${labels[p]}`} onClick={() => closeTab(index, p)}>
                      ×
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <div className="editor-controls">
            {file?.language === "markdown" && (
              <button
                title="Markdown: rendered preview or source"
                onClick={() =>
                  setMdSource((prev) => {
                    const next = new Set(prev);
                    if (next.has(file.path)) next.delete(file.path);
                    else next.add(file.path);
                    return next;
                  })
                }
              >
                {preview ? "Source" : "Preview"}
              </button>
            )}
            {last && (
              <>
                <label className="toggle" title="Turn off to practice like a CoderPad-style interview editor">
                  <input
                    type="checkbox"
                    checked={intellisense}
                    onChange={(e) => {
                      setIntellisenseOn(e.target.checked);
                      setIntellisense(e.target.checked);
                    }}
                  />
                  IntelliSense
                </label>
                <button disabled={dirtyPaths.size === 0} onClick={() => void saveAll()}>
                  Save{dirtyPaths.size > 0 ? ` (${dirtyPaths.size})` : ""}
                </button>
              </>
            )}
            {(last || split) && (
              <button
                className="split-toggle"
                title={split ? "Close this split (Ctrl/⌘+\\)" : "Split editor: two files side by side (Ctrl/⌘+\\)"}
                aria-label={split ? "Close split" : "Split editor"}
                onClick={() => toggleSplit(index === 0 ? 1 : 0)} // closing this side keeps the other side's file
              >
                {split ? "⊟" : "◫"}
              </button>
            )}
          </div>
        </div>
        <div className="editor-frame">
          {file ? (
            <Editor
              path={uriFor(file.path)}
              language={file.language}
              value={file.content}
              theme={dark ? "vs-dark" : "light"}
              onMount={onMountFor(index)}
              // Both panes can show the same file (one shared model): unmounting a pane must not dispose it.
              keepCurrentModel
              options={{
                ...intellisenseOptions(intellisense),
                readOnly: file.readOnly,
                fontSize: 14,
                fontFamily: '"JetBrains Mono", "Cascadia Code", "SF Mono", Consolas, Menlo, monospace',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: file.language === "python" ? 4 : 2,
                insertSpaces: true,
                detectIndentation: false,
                renderWhitespace: "boundary",
                rulers: file.language === "python" ? [100] : [],
                bracketPairColorization: { enabled: true },
                wordWrap: file.path.endsWith(".md") ? "on" : "off",
              }}
            />
          ) : (
            <p className="muted pad">Loading…</p>
          )}
          {/* Rendered over Monaco (which stays mounted) so switching tabs never recreates the editor. */}
          {file && preview && (
            <div className="md-preview markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{file.content}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <section className={`card editor-card ${tall ? "tall" : ""}`}>
      <div className="editor-body">
        {showTree ? (
          <>
            <div className="tree-wrap" style={{ width: treeWidth }}>
              <FileTree
                files={tree}
                activePath={panes[focusedPane].active}
                dirtyPaths={dirtyPaths}
                onOpen={(p) => void openFile(p)}
              />
            </div>
            <Splitter
              label="File tree"
              onDragStart={() => (dragStartWidth.current = treeWidth)}
              onDrag={(dx) => {
                const width = dragStartWidth.current + dx;
                if (width < TREE_COLLAPSE_BELOW) {
                  setShowTree(false);
                  return;
                }
                const clamped = Math.min(Math.max(width, TREE_MIN), 520);
                setTreeWidth(clamped);
                store(TREE_WIDTH_KEY, clamped);
              }}
              onDoubleClick={() => setShowTree(false)}
            />
          </>
        ) : (
          <button className="rail rail-left" title="Show files (Ctrl/⌘+B)" onClick={() => setShowTree(true)}>
            <span>›</span>
            <span className="rail-label">Files</span>
          </button>
        )}
        <div className="editor-panes" ref={panesEl}>
          {renderPane(panes[0], 0)}
          {split && (
            <>
              <Splitter
                label="Editor split"
                hint="drag to resize, double-click for 50/50"
                onDragStart={() => (dragStartRatio.current = splitRatio)}
                onDrag={(dx) => {
                  const width = panesEl.current?.clientWidth || 1;
                  const ratio = Math.min(Math.max(dragStartRatio.current + dx / width, 0.2), 0.8);
                  setSplitRatio(ratio);
                  store(SPLIT_RATIO_KEY, ratio);
                }}
                onDoubleClick={() => {
                  setSplitRatio(0.5);
                  store(SPLIT_RATIO_KEY, 0.5);
                }}
              />
              {renderPane(panes[1], 1)}
            </>
          )}
        </div>
      </div>

      <div className="editor-status">
        <span>{current?.readOnly ? `Read-only · ${current.path}` : current?.path}</span>
        <span className="muted">
          {status ||
            "Ctrl/⌘+S save · Ctrl/⌘+Enter save & run tests · Ctrl/⌘+\\ split · F12 / ⌘-click go to definition · Ctrl+Space suggest"}
        </span>
      </div>
    </section>
  );
}
