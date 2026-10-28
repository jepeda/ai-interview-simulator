export type Status = "not_started" | "in_progress" | "completed";

export interface ExerciseSummary {
  id: string;
  track: "syntax" | "debugging" | "project" | "interview";
  title: string;
  minutes: number;
  topics: string[];
  status: Status;
  last_passed: number | null;
  last_total: number | null;
}

export interface TestCase {
  suite: string;
  name: string;
  status: "passed" | "failed" | "error" | "skipped";
  message: string;
  details: string;
}

export interface RunResult {
  ok: boolean;
  passed: number;
  failed: number;
  total: number;
  cases: TestCase[];
  output: string;
  duration_s: number;
  ran_at: string;
}

export interface ExerciseDetail extends ExerciseSummary {
  requirements: string;
  files: { path: string; abs_path: string; modified: boolean }[];
  tests: { runner: string; path: string; abs_path: string }[];
  hints_total: number;
  quickref: string[]; // ids of the Quick ref pages relevant to this exercise
  hints: string[];
  attempts: number;
  times_completed: number;
  completed_at: string | null;
  last_result: RunResult | null;
}

export type EditorId = "vscode" | "webstorm" | "pycharm";

export interface Meta {
  interview_date: string | null; // YYYY-MM-DD, set from the top bar; null = no countdown
  repo_root: string;
  editors: { id: EditorId; label: string; available: boolean }[];
}

export interface EditorFile {
  path: string;
  content: string;
  language: "python" | "typescript" | "css" | "markdown" | "ini" | "json";
  read_only: boolean;
  mtime: number;
}

export interface CompletionItem {
  label: string;
  kind: string;
  detail: string;
  insert: string;
}

export interface Diagnostic {
  line: number;
  column: number;
  end_line: number;
  end_column: number;
  message: string;
  severity: "error" | "warning";
  code: string;
}

export interface QuickRefPage {
  id: string;
  title: string;
  markdown: string;
}

export interface TreeFile {
  path: string;
  read_only: boolean;
  pinned?: boolean; // shown above the folders (the generated REQUIREMENTS.md)
}

/** Generated, read-only brief the trainer serves for every exercise (not a file on disk). */
export const requirementsPath = (exerciseId: string) => `.trainer/${exerciseId}/REQUIREMENTS.md`;

export interface DefinitionTarget {
  path: string | null; // null = library code outside the repo
  line: number;
  column: number;
}

export interface SignatureInfo {
  label: string;
  doc: string;
  params: string[];
  active_param: number | null;
}

/** The mock-interview scenario on screen. Sent with every /api/interview call so the sandbox
 * (demo) scenario uses its own session slot and never touches a real interview. */
let interviewScenario: string | null = null;
export function setInterviewScenario(id: string | null): void {
  interviewScenario = id;
}
function scenarioHeader(url: string): Record<string, string> {
  return interviewScenario && url.startsWith("/api/interview") ? { "X-Interview-Scenario": interviewScenario } : {};
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...scenarioHeader(url), ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 300)}`);
  }
  return (await res.json()) as T;
}

const post = <T>(url: string, body?: unknown) =>
  request<T>(url, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const trainerApi = {
  meta: () => request<Meta>("/api/meta"),
  saveInterviewDate: (date: string | null) =>
    request<{ interview_date: string | null }>("/api/settings", { method: "PUT", body: JSON.stringify({ interview_date: date }) }),
  list: () => request<ExerciseSummary[]>("/api/exercises"),
  get: (id: string) => request<ExerciseDetail>(`/api/exercises/${id}`),
  run: (id: string) => post<ExerciseDetail>(`/api/exercises/${id}/run`),
  hint: (id: string) => post<ExerciseDetail>(`/api/exercises/${id}/hint`),
  complete: (id: string, completed: boolean) =>
    post<ExerciseDetail>(`/api/exercises/${id}/complete`, { completed }),
  reset: (id: string) => post<ExerciseDetail>(`/api/exercises/${id}/reset`),
  open: (path: string, editor: EditorId) =>
    post<{ opened: boolean; message: string }>("/api/open", { path, editor }),
  cheatsheet: () => request<{ markdown: string }>("/api/cheatsheet"),
  quickref: () => request<QuickRefPage[]>("/api/quickref"),
};

interface CodeRequest {
  path: string;
  content: string;
  line: number;
  column: number;
}

export const editorApi = {
  read: (path: string) => request<EditorFile>(`/api/editor/file?path=${encodeURIComponent(path)}`),
  tree: (exercise: string) =>
    request<{ root: string | null; files: TreeFile[] }>(`/api/editor/tree?exercise=${encodeURIComponent(exercise)}`),
  definition: (req: CodeRequest) => post<{ targets: DefinitionTarget[] }>("/api/editor/definition", req),
  save: (path: string, content: string) =>
    request<{ path: string; mtime: number }>("/api/editor/file", {
      method: "PUT",
      body: JSON.stringify({ path, content }),
    }),
  complete: (req: CodeRequest) => post<{ items: CompletionItem[] }>("/api/editor/complete", req),
  hover: (req: CodeRequest) => post<{ contents: string | null }>("/api/editor/hover", req),
  signature: (req: CodeRequest) => post<{ signatures: SignatureInfo[] }>("/api/editor/signature", req),
  lint: (path: string, content: string) => post<{ diagnostics: Diagnostic[] }>("/api/editor/lint", { path, content }),
};

/** vscode:// deep link: a fallback when the `code` CLI isn't on PATH. Works on Windows paths too. */
export function vscodeLink(absPath: string): string {
  return `vscode://file/${absPath.replace(/\\/g, "/")}`;
}

// ── mock AI interview ─────────────────────────────────────────────────────────

export interface InterviewFeature {
  id: string;
  title: string;
  summary: string;
  spec: string | null; // null until the bug is fixed
  tests: string[];
}

export interface InterviewConfig {
  id: string;
  title: string;
  order: number;
  sandbox: boolean; // demo scenario: not counted in "Your attempts"
  generated: boolean; // made with "Generate a new scenario"
  minutes: number;
  app_root: string; // e.g. backend/workspace/payouts
  portal_path: string; // e.g. /payouts.html
  portal_title: string;
  api_port: number;
  company_context: string;
  ticket: string;
  features: InterviewFeature[];
  claude_available: boolean;
}

export type Persona = "assistant" | "interviewer";

export interface InterviewEvent {
  t: string;
  elapsed: number; // seconds since the interview started
  kind: "start" | "prompt" | "reply" | "test_run" | "bug_fixed" | "feature_chosen" | "feature_done" | "note" | "code_change" | "data_reset" | "activity" | "idle" | "pause" | "resume" | "end" | "graded";
  [key: string]: unknown;
}

export interface InterviewSession {
  session_id: string;
  exercise: string;
  started_at: string;
  ended_at: string | null;
  stage: "bug" | "features";
  feature_id: string | null;
  feature_done?: boolean;
  paused_at?: string | null; // set while the clock is paused
  paused_seconds?: number; // total time spent paused (finished pauses)
  elapsed: number;
  events: InterviewEvent[];
  grade: string | null;
}

export interface InterviewScenario {
  id: string;
  title: string;
  order: number;
  minutes: number;
  sandbox: boolean;
}

export interface InterviewSnapshot {
  scenarios: InterviewScenario[];
  config: InterviewConfig;
  session: InterviewSession | null;
  /** The running (not ended) interview, whichever scenario it is. Only on GET. */
  active?: { scenario: string; session_id: string; elapsed: number } | null;
  result?: RunResult;
}

export interface PastSession {
  session_id: string;
  scenario: string;
  title: string;
  order: number;
  sandbox: boolean;
  elapsed: number;
  ended: boolean;
  prompts: number;
  assistant_prompts: number;
  notes: number;
  active_seconds: number;
  idle_seconds: number; // incl. time away from the window
  manual_lines: number; // lines added + removed by hand
  ai_lines: number; // ... and by the AI assistant
  test_runs: number;
  bug_fixed: boolean;
  bug_fixed_at: number | null;
  feature_done: boolean;
  feature_done_at: number | null;
  graded: boolean;
  verdict: string | null;
  scores: Record<string, number>;
}

/** A batch of attention/input samples from the interview page (see interviewActivity.ts). */
export interface ActivityReport {
  seconds: Record<string, number>; // active seconds per target: "file:<path>", "panel:<tab>", "header"
  idle: number;
  away: number; // window hidden or another app focused
  keys: Record<string, number>;
  clicks: Record<string, number>;
  scrolls: Record<string, number>;
  opened: { path: string; at: number }[];
  idle_gaps: { at: number; seconds: number; away: boolean }[];
}

/** Totals over a whole session (computed by the backend). */
export interface ActivitySummary {
  active: number;
  idle: number;
  away: number;
  keys: number;
  clicks: number;
  scrolls: number;
  targets: { target: string; seconds: number; keys: number; clicks: number; scrolls: number }[];
  files_opened: { path: string; at: number }[];
  idle_gaps: { at: number; seconds: number; away: boolean }[];
}

/** A "generate a new scenario" job (backend/trainer/generate.py). */
export interface GenerateJob {
  id: string;
  status: "running" | "verifying" | "ready" | "failed";
  company: string;
  domain: string;
  minutes: 30 | 60;
  difficulty: "warmup" | "standard" | "hard";
  pkg: string; // the scenario's exercise id once ready
  steps: number;
  last_tool: string | null;
  title: string | null;
  error: string | null;
  cost_usd: number | null;
  started_at: string;
  finished_at: string | null;
}

export const generateApi = {
  jobs: () => request<GenerateJob[]>("/api/generate"),
  start: (body: { company: string; domain: string; minutes: 30 | 60; difficulty: GenerateJob["difficulty"] }) =>
    post<GenerateJob>("/api/generate", body),
  dismiss: (id: string) => post<{ ok: boolean }>(`/api/generate/${id}/dismiss`),
  deleteScenario: (pkg: string) => request<{ ok: boolean }>(`/api/generate/scenario/${pkg}`, { method: "DELETE" }),
};

/** One server-sent event of a streamed Claude reply. */
export type ChatEvent =
  | { type: "start"; model: string }
  | { type: "text"; text: string }
  | { type: "tool"; name: string; target: string }
  | { type: "tool_error"; message: string }
  | { type: "error"; message: string }
  | { type: "done"; text: string; files_changed: string[]; cost_usd: number | null; duration_ms: number | null; cancelled: boolean };

/** POST and read a text/event-stream response, calling onEvent for each `data:` message. */
export async function streamPost(url: string, body: unknown, onEvent: (e: ChatEvent) => void): Promise<void> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...scenarioHeader(url) },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok || !res.body) {
    const text = await res.text();
    onEvent({ type: "error", message: `${res.status}: ${text.slice(0, 300)}` });
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut: number;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      if (chunk.startsWith("data: ")) onEvent(JSON.parse(chunk.slice(6)) as ChatEvent);
    }
  }
}

export const interviewApi = {
  get: (scenario: string) => request<InterviewSnapshot>(`/api/interview?scenario=${encodeURIComponent(scenario)}`),
  start: (scenario: string, resetCode: boolean) =>
    post<InterviewSnapshot>("/api/interview/start", { scenario, reset_code: resetCode }),
  end: () => post<InterviewSnapshot>("/api/interview/end"),
  run: () => post<InterviewSnapshot>("/api/interview/run"),
  chooseFeature: (featureId: string) => post<InterviewSnapshot>("/api/interview/feature", { feature_id: featureId }),
  note: (text: string, source: "typed" | "voice") => post<InterviewEvent>("/api/interview/note", { text, source }),
  diff: () => request<{ diff: string }>("/api/interview/diff"),
  resetData: () => post<{ ok: boolean }>("/api/interview/reset-data"),
  pause: () => post<InterviewSnapshot>("/api/interview/pause"),
  resume: () => post<InterviewSnapshot>("/api/interview/resume"),
  activity: (report: ActivityReport) => post<{ ok: boolean }>("/api/interview/activity", report),
  activitySummary: () => request<ActivitySummary>("/api/interview/activity"),
  sessions: () => request<PastSession[]>("/api/interview/sessions"),
  sessionGrade: (sessionId: string) => request<{ grade: string }>(`/api/interview/sessions/${encodeURIComponent(sessionId)}/grade`),
  cancel: (persona: Persona) => post<{ cancelled: boolean }>(`/api/interview/chat/cancel?persona=${persona}`),
  chat: (persona: Persona, message: string, activeFile: string | null, onEvent: (e: ChatEvent) => void) =>
    streamPost("/api/interview/chat", { persona, message, active_file: activeFile }, onEvent),
  grade: (onEvent: (e: ChatEvent) => void) => streamPost("/api/interview/grade", {}, onEvent),
};
