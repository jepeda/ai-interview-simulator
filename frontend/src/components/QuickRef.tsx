import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { trainerApi, type QuickRefPage } from "../api";

let cached: Promise<QuickRefPage[]> | null = null; // the pages never change while the app runs

function Page({ page, open }: { page: QuickRefPage; open: boolean }) {
  return (
    <details className="quickref-page" open={open}>
      <summary>{page.title}</summary>
      <div className="markdown">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{page.markdown}</ReactMarkdown>
      </div>
    </details>
  );
}

/** Super-short docs: this exercise's pages first, everything else below, plus a search box. */
export function QuickRef({ relevant }: { relevant: string[] }) {
  const [pages, setPages] = useState<QuickRefPage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    cached ??= trainerApi.quickref();
    cached.then(setPages).catch((e: Error) => {
      cached = null;
      setError(e.message);
    });
  }, []);

  if (error) return <p className="banner error">{error}</p>;

  const q = query.trim().toLowerCase();
  const matches = (p: QuickRefPage) => !q || `${p.title}\n${p.markdown}`.toLowerCase().includes(q);
  const byId = new Map(pages.map((p) => [p.id, p]));
  // While searching: title matches first, then the most mentions. Only the top result opens.
  const words = q.split(/\s+/).filter(Boolean);
  const rank = (p: QuickRefPage) => {
    const title = p.title.toLowerCase();
    const titleHits = words.filter((w) => title.includes(w)).length;
    return -(titleHits * 1000 + p.markdown.toLowerCase().split(q).length);
  };
  const mine = relevant.flatMap((id) => byId.get(id) ?? []).filter(matches);
  const others = pages
    .filter((p) => !relevant.includes(p.id))
    .filter(matches)
    .sort((a, b) => rank(a) - rank(b));

  return (
    <section className="card quickref">
      <input
        className="quickref-search"
        placeholder="Search docs… (get, sorted, Counter, is None)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && setQuery("")}
      />
      {mine.length > 0 && <h3 className="quickref-heading">For this exercise</h3>}
      {mine.map((p, i) => (
        <Page key={`${p.id}:${q}`} page={p} open={i === 0} />
      ))}
      {others.length > 0 && <h3 className="quickref-heading">{q ? "Other matches" : "Everything else"}</h3>}
      {others.map((p, i) => (
        <Page key={`${p.id}:${q}`} page={p} open={q !== "" && mine.length === 0 && i === 0} />
      ))}
      {q && mine.length + others.length === 0 && <p className="muted small">Nothing matches "{query}".</p>}
    </section>
  );
}
