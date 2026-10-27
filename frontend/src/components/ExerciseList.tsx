import type { ExerciseSummary } from "../api";

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
  return (
    <aside className="sidebar">
      {TRACKS.map((track) => {
        const items = exercises.filter((e) => e.track === track.key);
        const done = items.filter((e) => e.status === "completed").length;
        return (
          <section key={track.key}>
            <h3 className="sidebar-heading">
              {track.label}
              <span className="muted">
                {done}/{items.length}
              </span>
            </h3>
            <ul>
              {items.map((e) => (
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
