import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { trainerApi } from "../api";

function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function textOf(children: React.ReactNode): string {
  if (typeof children === "string" || typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(textOf).join("");
  if (children && typeof children === "object" && "props" in children) {
    return textOf((children as { props: { children?: React.ReactNode } }).props.children);
  }
  return "";
}

export function CheatSheet() {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    trainerApi
      .cheatsheet()
      .then((r) => setMarkdown(r.markdown))
      .catch((e: Error) => setError(e.message));
  }, []);

  const sections = useMemo(
    () => (markdown ?? "").split("\n").filter((l) => l.startsWith("## ")).map((l) => l.slice(3).trim()),
    [markdown],
  );

  if (error) return <div className="banner error">{error}</div>;
  if (markdown === null) return <p className="muted pad">Loading…</p>;

  return (
    <div className="layout">
      <aside className="sidebar toc">
        <h3 className="sidebar-heading">Sections</h3>
        <ul>
          {sections.map((s) => (
            <li key={s}>
              <a
                href={`#/cheatsheet`}
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById(slug(s))?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                {s}
              </a>
            </li>
          ))}
        </ul>
      </aside>
      <main className="content">
        <article className="card markdown cheatsheet">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{ h2: ({ children }) => <h2 id={slug(textOf(children))}>{children}</h2> }}
          >
            {markdown}
          </ReactMarkdown>
        </article>
      </main>
    </div>
  );
}
