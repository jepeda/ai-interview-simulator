import type { RunResult, TestCase } from "../api";

const ICON = { passed: "✓", failed: "✗", error: "!", skipped: "–" } as const;

/** "backend/tests/booking/test_p2_matching.py" -> "Part 2"; anything else -> its file name. */
function suiteLabel(suite: string): string {
  const name = suite.split("/").pop() ?? suite;
  const part = name.match(/^test_p(\d+)_/);
  return part ? `Part ${part[1]}` : name;
}

function groupBySuite(cases: TestCase[]) {
  const order: string[] = [];
  const bySuite = new Map<string, TestCase[]>();
  for (const c of cases) {
    if (!bySuite.has(c.suite)) {
      bySuite.set(c.suite, []);
      order.push(c.suite);
    }
    bySuite.get(c.suite)!.push(c);
  }
  return order.map((suite) => {
    const list = bySuite.get(suite)!;
    return { suite, label: suiteLabel(suite), cases: list, passed: list.filter((c) => c.status === "passed").length };
  });
}

function CaseRow({ c }: { c: TestCase }) {
  return (
    <li className={`case ${c.status}`}>
      {c.status === "passed" ? (
        <div className="case-line">
          <span className="case-icon">{ICON[c.status]}</span>
          <span className="case-name">{c.name}</span>
        </div>
      ) : (
        <details>
          <summary className="case-line">
            <span className="case-icon">{ICON[c.status]}</span>
            <span className="case-name">{c.name}</span>
            {c.message && <span className="case-msg">{c.message}</span>}
          </summary>
          {c.details && <pre className="trace">{c.details}</pre>}
        </details>
      )}
    </li>
  );
}

export function TestResults({ result, running }: { result: RunResult | null; running: boolean }) {
  if (!result) {
    return (
      <section className="card">
        <h2>Test results</h2>
        <p className="muted">{running ? "Running…" : "Not run yet. Edit the code above, then press Ctrl/⌘+Enter to save and run the tests."}</p>
      </section>
    );
  }

  const pct = result.total ? Math.round((result.passed / result.total) * 100) : 0;
  const groups = groupBySuite(result.cases);

  return (
    <section className={`card results ${running ? "stale" : ""}`}>
      <h2>
        Test results{" "}
        <span className={`result-badge ${result.ok ? "pass" : "fail"}`}>
          {result.ok ? "All passing" : `${result.failed} failing`}
        </span>
      </h2>
      <div className="result-bar" aria-label={`${result.passed} of ${result.total} passed`}>
        <div className="result-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="muted small">
        {result.passed}/{result.total} passed · {result.duration_s}s · {new Date(result.ran_at).toLocaleTimeString()}
      </p>
      {groups.map((group) => (
        <div key={group.suite} className="case-group">
          {groups.length > 1 && (
            <h3 className={`group-heading ${group.passed === group.cases.length ? "pass" : "fail"}`}>
              <span>{group.label}</span>
              <span className="muted small">{group.suite.split("/").pop()}</span>
              <span className="group-score">
                {group.passed}/{group.cases.length}
              </span>
            </h3>
          )}
          <ul className="cases">
            {group.cases.map((c, i) => (
              <CaseRow key={i} c={c} />
            ))}
          </ul>
        </div>
      ))}
      <details className="raw-output">
        <summary>Raw test output</summary>
        <pre className="trace">{result.output}</pre>
      </details>
    </section>
  );
}
