"""Run an exercise's test suites in a subprocess and normalize the results.

pytest results come from its JUnit XML report and vitest results from its JSON reporter, so
nothing depends on parsing console output. Both are invoked through absolute interpreter paths
(sys.executable / node), which avoids PATH and .cmd-shim problems on Windows.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from trainer.catalog import Exercise, TestSuite
from trainer.paths import FRONTEND_DIR, REPO_ROOT

TIMEOUT_SECONDS = 120
OUTPUT_LIMIT = 8000
_lock = threading.Lock()  # one test run at a time


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        PYTHONIOENCODING="utf-8",
        PYTHONUTF8="1",
        PYTHONDONTWRITEBYTECODE="1",
        NO_COLOR="1",
        FORCE_COLOR="0",
        CI="1",
    )
    return env


def _case(suite: str, name: str, status: str, message: str = "", details: str = "") -> dict:
    return {"suite": suite, "name": name, "status": status, "message": message, "details": details}


def _summary_line(message: str, details: str) -> str:
    first = (message or "").strip().splitlines()[0] if (message or "").strip() else ""
    if first and first not in {"collection failure", "failed on setup with"}:
        return first[:300]
    lines = [ln.strip() for ln in (details or "").splitlines() if ln.strip()]
    errors = [ln for ln in lines if ln.startswith("E ")]
    return (errors[-1][2:].strip() if errors else (lines[-1] if lines else first))[:300]


def _suite_of(module_dotted: str, suites: list[TestSuite]) -> str:
    """'backend.tests.booking.test_p1_availability' -> the matching suite path."""
    as_path = module_dotted.replace(".", "/") + ".py"
    return next((s.path for s in suites if s.path == as_path), suites[0].path)


def _run_pytest(suites: list[TestSuite], tmp: Path) -> tuple[list[dict], str, int]:
    """All pytest suites of an exercise in ONE process (interpreter + import startup paid once)."""
    report = tmp / "pytest.xml"
    cmd = [
        sys.executable, "-m", "pytest", *(s.path for s in suites),
        "-q", "--tb=short", "-p", "no:cacheprovider",
        f"--junitxml={report}", "-o", "junit_family=xunit1",
    ]
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=TIMEOUT_SECONDS, env=_env(),
    )
    output = proc.stdout + proc.stderr
    cases: list[dict] = []
    if report.exists():
        for tc in ET.parse(report).getroot().iter("testcase"):
            name = tc.get("name", "?")
            classname = tc.get("classname", "")
            # Collection errors have no classname; their name is the module path.
            suite = _suite_of(classname or name, suites)
            label = name if classname else f"collect {name.rsplit('.', 1)[-1]}"
            failure = tc.find("failure")
            error = tc.find("error")
            skipped = tc.find("skipped")
            if failure is not None or error is not None:
                node = failure if failure is not None else error
                details = node.text or ""
                status = "failed" if failure is not None else "error"
                cases.append(_case(suite, label, status, _summary_line(node.get("message", ""), details), details))
            elif skipped is not None:
                cases.append(_case(suite, label, "skipped", skipped.get("message", "")))
            else:
                cases.append(_case(suite, label, "passed"))
    if not cases:
        cases.append(_case(suites[0].path, "pytest", "error", "pytest produced no results", output[-3000:]))
    # Keep the catalog's suite order (Part 1, Part 2, ...).
    order = {s.path: i for i, s in enumerate(suites)}
    cases.sort(key=lambda c: order.get(c["suite"], 0))
    return cases, output, proc.returncode


def _run_vitest(suite: TestSuite, tmp: Path) -> tuple[list[dict], str, int]:
    node = shutil.which("node")
    vitest = FRONTEND_DIR / "node_modules" / "vitest" / "vitest.mjs"
    if node is None or not vitest.exists():
        msg = "Node.js or frontend dependencies are missing. Run setup again."
        return [_case(suite.path, "vitest", "error", msg)], msg, 1

    report = tmp / "vitest.json"
    test_rel = (REPO_ROOT / suite.path).relative_to(FRONTEND_DIR).as_posix()
    cmd = [node, str(vitest), "run", test_rel, "--reporter=json", f"--outputFile={report}"]
    proc = subprocess.run(
        cmd, cwd=FRONTEND_DIR, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=TIMEOUT_SECONDS, env=_env(),
    )
    output = proc.stdout + proc.stderr
    cases: list[dict] = []
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
        for file_result in data.get("testResults", []):
            assertions = file_result.get("assertionResults", [])
            for a in assertions:
                status = {"passed": "passed", "failed": "failed"}.get(a.get("status"), "skipped")
                details = "\n".join(a.get("failureMessages") or [])
                cases.append(
                    _case(suite.path, a.get("fullName") or a.get("title", "?"), status,
                          _summary_line(details, details), details)
                )
            if not assertions and file_result.get("status") == "failed":
                message = file_result.get("message", "")
                cases.append(_case(suite.path, "load test file", "error", _summary_line(message, message), message))
    if not cases:
        cases.append(_case(suite.path, "vitest", "error", "vitest produced no results", output[-3000:]))
    return cases, output, proc.returncode


def run_exercise(exercise: Exercise) -> dict:
    started = time.perf_counter()
    all_cases: list[dict] = []
    outputs: list[str] = []
    with _lock, tempfile.TemporaryDirectory(prefix="trainer-") as tmp_name:
        tmp = Path(tmp_name)
        batches: list[tuple[str, list[TestSuite]]] = []
        pytest_suites = [t for t in exercise.tests if t.runner == "pytest"]
        if pytest_suites:
            batches.append(("pytest", pytest_suites))
        batches += [("vitest", [t]) for t in exercise.tests if t.runner == "vitest"]
        for runner_name, suites in batches:
            try:
                if runner_name == "pytest":
                    cases, output, _ = _run_pytest(suites, tmp)
                else:
                    cases, output, _ = _run_vitest(suites[0], tmp)
            except subprocess.TimeoutExpired:
                cases = [_case(suites[0].path, runner_name, "error",
                               f"Timed out after {TIMEOUT_SECONDS}s (infinite loop or a coroutine that never finishes?)")]
                output = ""
            all_cases.extend(cases)
            outputs.append(f"$ {runner_name} {' '.join(s.path for s in suites)}\n{output.strip()}")

    counts = {s: sum(1 for c in all_cases if c["status"] == s) for s in ("passed", "failed", "error", "skipped")}
    output = "\n\n".join(outputs)
    return {
        "ok": counts["passed"] > 0 and counts["failed"] == 0 and counts["error"] == 0,
        "passed": counts["passed"],
        "failed": counts["failed"] + counts["error"],
        "total": len(all_cases),
        "cases": all_cases,
        "output": output[-OUTPUT_LIMIT:],
        "duration_s": round(time.perf_counter() - started, 2),
        "ran_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
