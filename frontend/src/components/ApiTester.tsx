import { useEffect, useMemo, useState } from "react";

/**
 * A small Postman-style API tester for an exercise's FastAPI service. Endpoints come from the
 * service's own OpenAPI spec (so new routes show up automatically); picking one pre-fills the
 * method, the URL (path params as `{name}`, required query params) and an example JSON body built
 * from its schema. Requests go through the dev-server proxy (`base`, e.g. /booking-api).
 */

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
const METHODS: Method[] = ["GET", "POST", "PUT", "PATCH", "DELETE"];

export interface Endpoint {
  method: Method;
  path: string;
  summary: string;
  url: string; // pre-filled URL: path + required query params
  body: string; // pre-filled JSON body ("" when none)
}

interface Sent {
  method: Method;
  url: string;
  body: string;
  status: number;
  ms: number;
  response: string;
  at: number;
}

export type Schema = {
  $ref?: string;
  type?: string;
  format?: string;
  properties?: Record<string, Schema>;
  required?: string[];
  items?: Schema;
  enum?: unknown[];
  anyOf?: Schema[];
  default?: unknown;
  example?: unknown;
  examples?: unknown[];
};
export type Spec = {
  paths: Record<string, Record<string, { summary?: string; parameters?: { name: string; in: string; required?: boolean; schema?: Schema }[]; requestBody?: { content?: Record<string, { schema?: Schema }> } }>>;
  components?: { schemas?: Record<string, Schema> };
};

export function exampleValue(schema: Schema | undefined, spec: Spec, name = "", depth = 0): unknown {
  if (!schema || depth > 4) return null;
  if (schema.$ref) return exampleValue(spec.components?.schemas?.[schema.$ref.split("/").pop() ?? ""], spec, name, depth + 1);
  if (schema.example !== undefined) return schema.example;
  if (schema.examples?.length) return schema.examples[0];
  if (schema.default !== undefined) return schema.default;
  if (schema.enum?.length) return schema.enum[0];
  if (schema.anyOf?.length) return exampleValue(schema.anyOf.find((s) => s.type !== "null") ?? schema.anyOf[0], spec, name, depth + 1);
  switch (schema.type) {
    case "object": {
      const out: Record<string, unknown> = {};
      for (const [key, prop] of Object.entries(schema.properties ?? {})) out[key] = exampleValue(prop, spec, key, depth + 1);
      return out;
    }
    case "array":
      return [exampleValue(schema.items, spec, name, depth + 1)];
    case "integer":
      return 1;
    case "number":
      return 1.0;
    case "boolean":
      return true;
    case "string":
      if (schema.format === "date-time") return "2026-11-02T09:00:00-05:00";
      if (schema.format === "date") return "2026-11-02";
      return name.includes("key") ? `key-${Math.random().toString(36).slice(2, 10)}` : "string";
    default:
      return null;
  }
}

export function endpointsOf(spec: Spec): Endpoint[] {
  const out: Endpoint[] = [];
  for (const [path, ops] of Object.entries(spec.paths)) {
    for (const [method, op] of Object.entries(ops)) {
      const upper = method.toUpperCase() as Method;
      if (!METHODS.includes(upper)) continue;
      const query = (op.parameters ?? [])
        .filter((p) => p.in === "query" && p.required)
        .map((p) => `${p.name}=${encodeURIComponent(String(exampleValue(p.schema, spec, p.name) ?? ""))}`);
      const schema = op.requestBody?.content?.["application/json"]?.schema;
      out.push({
        method: upper,
        path,
        summary: op.summary ?? "",
        url: path + (query.length ? `?${query.join("&")}` : ""),
        body: schema ? JSON.stringify(exampleValue(schema, spec), null, 2) : "",
      });
    }
  }
  return out;
}

function pretty(text: string): string {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

export function ApiTester({ base, docs }: { base: string; docs: string }) {
  const historyKey = `trainer.apiTester${base}`;
  const [spec, setSpec] = useState<Spec | null>(null);
  const [specError, setSpecError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [method, setMethod] = useState<Method>("GET");
  const [url, setUrl] = useState("/health");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [last, setLast] = useState<Sent | null>(null);
  const [history, setHistory] = useState<Sent[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(historyKey) ?? "[]") as Sent[];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    fetch(`${base}/openapi.json`)
      .then((r) => (r.ok ? (r.json() as Promise<Spec>) : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setSpec)
      .catch(() => setSpecError(`Can't load the API's spec from ${base}/openapi.json. Is \`npm run dev\` running?`));
  }, [base]);

  const endpoints = useMemo(() => (spec ? endpointsOf(spec) : []), [spec]);
  const shown = endpoints.filter((e) => `${e.method} ${e.path} ${e.summary}`.toLowerCase().includes(filter.toLowerCase()));

  async function send() {
    setSending(true);
    const started = performance.now();
    let sent: Sent;
    try {
      const res = await fetch(base + url, {
        method,
        headers: body.trim() ? { "Content-Type": "application/json" } : undefined,
        body: method !== "GET" && body.trim() ? body : undefined,
      });
      sent = { method, url, body, status: res.status, ms: Math.round(performance.now() - started), response: pretty(await res.text()), at: Date.now() };
    } catch (e) {
      sent = { method, url, body, status: 0, ms: Math.round(performance.now() - started), response: `Request failed: ${(e as Error).message}`, at: Date.now() };
    }
    setLast(sent);
    setHistory((prev) => {
      const next = [sent, ...prev].slice(0, 20);
      try {
        localStorage.setItem(historyKey, JSON.stringify(next));
      } catch {
        // not remembered across reloads
      }
      return next;
    });
    setSending(false);
  }

  const restore = (r: { method: Method; url: string; body: string }) => {
    setMethod(r.method);
    setUrl(r.url);
    setBody(r.body);
  };

  return (
    <div className="api-tester">
      <section className="card">
        <div className="api-request">
          <select value={method} onChange={(e) => setMethod(e.target.value as Method)} className={`method m-${method.toLowerCase()}`}>
            {METHODS.map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
          <span className="api-base muted">{base}</span>
          <input
            className="api-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void send();
            }}
            spellCheck={false}
          />
          <button className="primary" disabled={sending} onClick={() => void send()}>
            {sending ? "…" : "Send"}
          </button>
        </div>
        {method !== "GET" && (
          <textarea
            className="api-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="JSON body"
            rows={Math.min(12, Math.max(3, body.split("\n").length))}
            spellCheck={false}
          />
        )}
        <p className="muted small">
          Replace any <code>{"{path_param}"}</code> in the URL, then press Enter or Send.{" "}
          <a href={docs} target="_blank" rel="noreferrer">
            Swagger ↗
          </a>
        </p>
      </section>

      {last && (
        <section className="card">
          <div className="api-response-head">
            <span className={`status s${String(last.status)[0]}`}>{last.status || "ERR"}</span>
            <span className="muted small">
              {last.method} {last.url} · {last.ms} ms
            </span>
          </div>
          <pre className="api-response">{last.response}</pre>
        </section>
      )}

      <section className="card">
        <h3>Endpoints</h3>
        {specError && <div className="banner error small">{specError}</div>}
        {endpoints.length > 6 && <input className="api-filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter…" />}
        <ul className="api-endpoints">
          {shown.map((e) => (
            <li key={`${e.method} ${e.path}`}>
              <button onClick={() => restore(e)} title="Fill in the request">
                <span className={`method m-${e.method.toLowerCase()}`}>{e.method}</span> <code>{e.path}</code>{" "}
                <span className="muted small">{e.summary}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {history.length > 0 && (
        <section className="card">
          <h3>
            History{" "}
            <button
              className="ghost small"
              onClick={() => {
                setHistory([]);
                localStorage.removeItem(historyKey);
              }}
            >
              Clear
            </button>
          </h3>
          <ul className="api-endpoints">
            {history.map((h) => (
              <li key={h.at}>
                <button onClick={() => restore(h)} title="Load this request again">
                  <span className={`status s${String(h.status)[0]}`}>{h.status || "ERR"}</span> <span className={`method m-${h.method.toLowerCase()}`}>{h.method}</span>{" "}
                  <code>{h.url}</code>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
