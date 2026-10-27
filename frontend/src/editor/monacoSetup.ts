/**
 * One-time Monaco configuration.
 *
 * - Monaco is bundled from node_modules (no CDN), so the editor works offline.
 * - TypeScript IntelliSense comes from Monaco's built-in TS worker.
 * - Python IntelliSense comes from the trainer API (Jedi running in the project's .venv).
 */
import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/editor/editor.worker?worker";
import TsWorker from "monaco-editor/language/typescript/ts.worker?worker";
import { editorApi, type CompletionItem } from "../api";

self.MonacoEnvironment = {
  getWorker(_workerId: string, label: string) {
    return label === "typescript" || label === "javascript" ? new TsWorker() : new EditorWorker();
  },
};
loader.config({ monaco });

// ── IntelliSense on/off (practice "interview mode" with it off) ─────────────────
const PREF_KEY = "trainer.intellisense";
let intellisenseOn = (() => {
  try {
    return localStorage.getItem(PREF_KEY) !== "off";
  } catch {
    return true;
  }
})();

export function isIntellisenseOn(): boolean {
  return intellisenseOn;
}

export function setIntellisenseOn(on: boolean): void {
  intellisenseOn = on;
  try {
    localStorage.setItem(PREF_KEY, on ? "on" : "off");
  } catch {
    /* storage unavailable: preference lasts for this tab only */
  }
}

/** Editor options that switch every suggestion UI on or off (Python and TypeScript alike). */
export function intellisenseOptions(on: boolean): monaco.editor.IEditorOptions {
  return {
    quickSuggestions: on ? { other: true, comments: false, strings: false } : false,
    suggestOnTriggerCharacters: on,
    parameterHints: { enabled: on },
    hover: { enabled: on ? "on" : "off" },
  };
}

// ── models <-> repo paths ─────────────────────────────────────────────────────────
export const uriFor = (repoPath: string) => `file:///${repoPath}`;
const pathOf = (model: monaco.editor.ITextModel) => model.uri.path.replace(/^\//, "");

// ── TypeScript (dbg5 frontend file) ───────────────────────────────────────────────
monaco.typescript.typescriptDefaults.setCompilerOptions({
  target: monaco.typescript.ScriptTarget.ES2020,
  module: monaco.typescript.ModuleKind.ESNext,
  moduleResolution: monaco.typescript.ModuleResolutionKind.NodeJs,
  strict: true,
  noEmit: true,
  allowNonTsExtensions: true,
});

let typesLoaded = false;
/** patientState.ts imports "./types": give the TS worker that file so types resolve. */
export async function ensureClinicTypes(): Promise<void> {
  if (typesLoaded) return;
  typesLoaded = true;
  const file = await editorApi.read("frontend/src/clinic/types.ts");
  monaco.typescript.typescriptDefaults.addExtraLib(file.content, uriFor(file.path));
}

// ── Python providers ──────────────────────────────────────────────────────────────
const K = monaco.languages.CompletionItemKind;
const KIND: Record<string, monaco.languages.CompletionItemKind> = {
  module: K.Module,
  class: K.Class,
  instance: K.Variable,
  function: K.Function,
  param: K.Variable,
  path: K.File,
  keyword: K.Keyword,
  property: K.Property,
  statement: K.Variable,
};

function codeRequest(model: monaco.editor.ITextModel, position: monaco.Position) {
  return { path: pathOf(model), content: model.getValue(), line: position.lineNumber, column: position.column };
}

monaco.languages.registerCompletionItemProvider("python", {
  triggerCharacters: ["."],
  async provideCompletionItems(model, position) {
    if (!intellisenseOn) return { suggestions: [] };
    let items: CompletionItem[] = [];
    try {
      items = (await editorApi.complete(codeRequest(model, position))).items;
    } catch {
      return { suggestions: [] };
    }
    const word = model.getWordUntilPosition(position);
    const range = new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn);
    return {
      suggestions: items.map((item, i) => ({
        label: item.label,
        kind: KIND[item.kind] ?? K.Text,
        detail: item.detail,
        insertText: item.insert,
        range,
        sortText: String(i).padStart(4, "0"), // keep Jedi's ranking
      })),
    };
  },
});

monaco.languages.registerHoverProvider("python", {
  async provideHover(model, position) {
    if (!intellisenseOn || !model.getWordAtPosition(position)) return null;
    try {
      const { contents } = await editorApi.hover(codeRequest(model, position));
      return contents ? { contents: [{ value: contents }] } : null;
    } catch {
      return null;
    }
  },
});

monaco.languages.registerSignatureHelpProvider("python", {
  signatureHelpTriggerCharacters: ["(", ","],
  signatureHelpRetriggerCharacters: [")"],
  async provideSignatureHelp(model, position) {
    if (!intellisenseOn) return null;
    try {
      const { signatures } = await editorApi.signature(codeRequest(model, position));
      if (signatures.length === 0) return null;
      return {
        value: {
          signatures: signatures.map((s) => ({
            label: s.label,
            documentation: s.doc ? { value: s.doc } : undefined,
            parameters: s.params.map((p) => ({ label: p })),
          })),
          activeSignature: 0,
          activeParameter: signatures[0].active_param ?? 0,
        },
        dispose() {},
      };
    } catch {
      return null;
    }
  },
});

// ── Go to definition (F12 / Cmd+click) across files ─────────────────────────────────
type Opener = (path: string, line: number, column: number) => void;
let activeOpener: Opener | null = null;

/** The mounted CodeEditor registers how to open a file in a tab (there is one editor at a time). */
export function setFileOpener(opener: Opener | null): void {
  activeOpener = opener;
}

monaco.editor.registerEditorOpener({
  openCodeEditor(_source, resource, selectionOrPosition) {
    if (!activeOpener || resource.scheme !== "file") return false;
    const pos =
      selectionOrPosition && "startLineNumber" in selectionOrPosition
        ? { line: selectionOrPosition.startLineNumber, column: selectionOrPosition.startColumn }
        : { line: selectionOrPosition?.lineNumber ?? 1, column: selectionOrPosition?.column ?? 1 };
    activeOpener(resource.path.replace(/^\//, ""), pos.line, pos.column);
    return true;
  },
});

/** Make sure a model exists for a repo file so Monaco can peek/jump into it. */
async function ensureModel(path: string): Promise<monaco.Uri | null> {
  const uri = monaco.Uri.parse(uriFor(path));
  if (monaco.editor.getModel(uri)) return uri;
  try {
    const file = await editorApi.read(path);
    if (!monaco.editor.getModel(uri)) monaco.editor.createModel(file.content, file.language, uri);
    return uri;
  } catch {
    return null; // not an exercise file (e.g. library code): nothing to open
  }
}

monaco.languages.registerDefinitionProvider("python", {
  async provideDefinition(model, position) {
    try {
      const { targets } = await editorApi.definition(codeRequest(model, position));
      const locations: monaco.languages.Location[] = [];
      for (const t of targets) {
        if (!t.path) continue;
        const uri = await ensureModel(t.path);
        if (uri) locations.push({ uri, range: new monaco.Range(t.line, t.column, t.line, t.column) });
      }
      return locations;
    } catch {
      return [];
    }
  },
});

// ── Diagnostics (Python): Jedi syntax errors + Ruff ─────────────────────────────────
export async function lintModel(model: monaco.editor.ITextModel): Promise<void> {
  if (model.getLanguageId() !== "python" || model.isDisposed()) return;
  const versionAtRequest = model.getVersionId();
  try {
    const { diagnostics } = await editorApi.lint(pathOf(model), model.getValue());
    if (model.isDisposed() || model.getVersionId() !== versionAtRequest) return; // stale result
    monaco.editor.setModelMarkers(
      model,
      "trainer",
      diagnostics.map((d) => ({
        startLineNumber: d.line,
        startColumn: d.column,
        endLineNumber: d.end_line,
        endColumn: Math.max(d.end_column, d.column + 1),
        message: d.code === "syntax" ? d.message : `${d.message} (${d.code})`,
        severity: d.severity === "error" ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning,
      })),
    );
  } catch {
    /* lint is best-effort */
  }
}

export { monaco };
