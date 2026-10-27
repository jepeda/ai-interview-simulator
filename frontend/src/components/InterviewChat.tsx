import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { interviewApi, type ChatEvent, type InterviewEvent, type Persona } from "../api";

interface Tool {
  name: string;
  target: string;
}

export interface ChatMessage {
  role: "user" | "claude";
  text: string;
  tools: Tool[];
  error?: string;
  filesChanged?: string[];
  meta?: string;
  pending?: boolean;
}

/** Rebuild a persona's conversation from the session log (so it survives reloads). */
export function messagesFromEvents(events: InterviewEvent[], persona: Persona): ChatMessage[] {
  const out: ChatMessage[] = [];
  for (const e of events) {
    if (e.persona !== persona) continue;
    if (e.kind === "prompt") out.push({ role: "user", text: String(e.text ?? ""), tools: [] });
    if (e.kind === "reply")
      out.push({
        role: "claude",
        text: String(e.text ?? ""),
        tools: (e.tools as Tool[]) ?? [],
        filesChanged: (e.files_changed as string[]) ?? [],
        meta: e.cancelled ? "stopped" : undefined,
      });
  }
  return out;
}

const PLACEHOLDER: Record<Persona, string> = {
  assistant: "Ask the AI assistant… it can read and edit the codebase (Enter to send, Shift+Enter for a new line)",
  interviewer: "Ask the interviewer a domain or product question, or talk through your plan…",
};

const STARTERS: Record<Persona, string[]> = {
  assistant: [
    "Give me a quick tour of this codebase: entry points, layers and conventions.",
    "How do I run the app and the tests here?",
  ],
  interviewer: [
    "Who uses this screen, and what do they need to decide from it?",
    "How many users are affected, and has anyone already been paid wrong?",
  ],
};

interface Props {
  persona: Persona;
  initial: ChatMessage[];
  disabled: boolean;
  /** Called before sending (save editor files so Claude sees them) and after a reply (reload files). */
  beforeSend: () => Promise<string | null>;
  afterReply: (filesChanged: string[]) => void;
}

export function InterviewChat({ persona, initial, disabled, beforeSend, afterReply }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [model, setModel] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setDraft("");
    setBusy(true);
    const activeFile = await beforeSend();
    setMessages((m) => [...m, { role: "user", text: message, tools: [] }, { role: "claude", text: "", tools: [], pending: true }]);
    const update = (change: (last: ChatMessage) => ChatMessage) =>
      setMessages((m) => [...m.slice(0, -1), change(m[m.length - 1])]);
    let changed: string[] = [];
    await interviewApi
      .chat(persona, message, activeFile, (e: ChatEvent) => {
        if (e.type === "start") setModel(e.model);
        else if (e.type === "text") update((last) => ({ ...last, text: last.text + e.text }));
        else if (e.type === "tool") update((last) => ({ ...last, tools: [...last.tools, { name: e.name, target: e.target }] }));
        else if (e.type === "error") update((last) => ({ ...last, error: e.message }));
        else if (e.type === "done") {
          changed = e.files_changed;
          const secs = e.duration_ms ? `${Math.round(e.duration_ms / 1000)}s` : "";
          update((last) => ({
            ...last,
            text: last.text || e.text,
            pending: false,
            filesChanged: e.files_changed,
            meta: e.cancelled ? "stopped" : secs,
          }));
        }
      })
      .catch((err: Error) => update((last) => ({ ...last, pending: false, error: err.message })));
    setMessages((m) => m.map((x) => (x.pending ? { ...x, pending: false } : x)));
    setBusy(false);
    afterReply(changed);
  }

  return (
    <div className="chat">
      <div className="chat-log" ref={listRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="muted small">
              {persona === "assistant"
                ? "This is the AI assistant built into the IDE. It can read, search and edit the payouts codebase and run the backend tests. Every prompt is logged for the review."
                : "This is your interviewer. Ask about the domain, the users and the requirements, and narrate your plan. They won't hand you the answer."}
            </p>
            {STARTERS[persona].map((s) => (
              <button key={s} className="chat-suggestion" disabled={disabled} onClick={() => void send(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.tools.length > 0 && (
              <div className="chat-tools">
                {m.tools.map((t, j) => (
                  <span key={j} className={`tool-chip ${["Edit", "Write", "MultiEdit"].includes(t.name) ? "edit" : ""}`} title={t.target}>
                    {t.name} {t.target && <span className="muted">{t.target.split("/").slice(-2).join("/")}</span>}
                  </span>
                ))}
              </div>
            )}
            {m.text ? (
              <div className="markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
              </div>
            ) : (
              m.pending && <span className="muted small typing">{m.tools.length ? "working…" : "thinking…"}</span>
            )}
            {m.error && <div className="chat-error">{m.error}</div>}
            {(m.meta || (m.filesChanged && m.filesChanged.length > 0)) && (
              <div className="chat-meta muted small">
                {m.filesChanged && m.filesChanged.length > 0 && <>edited {m.filesChanged.map((f) => f.split("/").pop()).join(", ")} · </>}
                {m.meta}
              </div>
            )}
          </div>
        ))}
      </div>
      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          void send(draft);
        }}
      >
        <textarea
          value={draft}
          rows={3}
          disabled={disabled}
          placeholder={disabled ? "The interview has ended." : PLACEHOLDER[persona]}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              void send(draft);
            }
          }}
        />
        <div className="chat-actions">
          <span className="muted small">{model ? `model: ${model}` : persona === "assistant" ? "Claude Code · logged" : "interviewer · logged"}</span>
          {busy ? (
            <button type="button" onClick={() => void interviewApi.cancel(persona)}>
              ■ Stop
            </button>
          ) : (
            <button type="submit" className="primary" disabled={disabled || !draft.trim()}>
              Send
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
