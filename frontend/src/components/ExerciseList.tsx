import { useState } from "react";
import type { ExerciseSummary } from "../api";

const COLLAPSED_KEY = "trainer.collapsedSections";

function readCollapsed(): string[] {
  try {
    return JSON.parse(localStorage.getItem(COLLAPSED_KEY) ?? "[]") as string[];
  } catch {
    return [];
  }
}

const TRACKS: { key: ExerciseSummary["track"]; label: string }[] = [
  { key: "syntax", label: "Python syntax drills" },
  { key: "debugging", label: "FastAPI debugging (clinic app)" },
  { key: "project", label: "Interview project (60–90 min)" },
  { key: "interview", label: "Mock AI interview (timed)" },
];

export function StatusDot({ status }: { status: ExerciseSummary["status"] }) {
  const label = { not_started: "Not started", in_progress: "In progress", completed: "Completed" }[status];
  return <span className={`dot ${status}`} title={label} aria-label={label} />;
}

export function ExerciseList({ exercises, selectedId }: { exercises: ExerciseSummary[]; selectedId: string | null }) {
  const [collapsed, setCollapsed] = useState<string[]>(readCollapsed);
  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key];
      try {
        localStorage.setItem(COLLAPSED_KEY, JSON.stringify(next));
      } catch {
        // private window etc.: just don't remember it
      }
      return next;
    });

  return (
    <aside className="sidebar">
      {TRACKS.map((track) => {
        const items = exercises.filter((e) => e.track === track.key);
        const done = items.filter((e) => e.status === "completed").length;
        const closed = collapsed.includes(track.key);
        // A collapsed section still shows the exercise you're on, so you never lose your place.
        const shown = closed ? items.filter((e) => e.id === selectedId) : items;
        return (
          <section key={track.key}>
            <h3 className="sidebar-heading">
              <button className="section-toggle" aria-expanded={!closed} onClick={() => toggle(track.key)}>
                <span className="chevron">{closed ? "▸" : "▾"}</span>
                {track.label}
                <span className="muted">
                  {done}/{items.length}
                </span>
              </button>
            </h3>
            <ul>
              {shown.map((e) => (
                <li key={e.id}>
                  <a href={`#/ex/${e.id}`} className={e.id === selectedId ? "selected" : ""}>
                    <StatusDot status={e.status} />
                    <span className="ex-id">{e.id}</span>
                    <span className="ex-title">{e.title}</span>
                    {e.last_total !== null && e.status !== "completed" && (
                      <span className="score">
                        {e.last_passed}/{e.last_total}
                      </span>
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </aside>
  );
}
