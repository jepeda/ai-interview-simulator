"""Generate a new mock-interview scenario with Claude Code.

A background job runs the `claude` CLI headless, allowed to write only into the reserved folders of
one new scenario package (`gen_<name>`). It builds a small full-stack app with a user-reported bug,
the bug's tests, feature requests with their tests, a reference solution and hidden interviewer
notes, modeled on the stock scenarios, and writes the scenario's config as a *draft*. The trainer
then runs the content check itself (every starter fails, every solution passes) and only publishes
a scenario that passes; a failed one is removed. You never see the bug: progress shows step counts
and tool names only.

Generated scenarios are gitignored (see .gitignore): they're yours, and full of spoilers.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from trainer import interview
from trainer.catalog import load_catalog
from trainer.paths import (
    DATA_DIR,
    GEN_STARTERS_DIR,
    GEN_WEB_STARTERS_DIR,
    GEN_WEB_WORKSPACE_DIR,
    GEN_WORKSPACE_DIR,
    GENERATED_CONFIG_DIR,
    REPO_ROOT,
    SOLUTIONS_DIR,
)
from trainer.workspace import init_workspace

router = APIRouter(prefix="/api/generate", tags=["generate"])

JOBS_DIR = DATA_DIR / "generate"
JOBS_PATH = JOBS_DIR / "jobs.json"
FIRST_PORT = 8720
JOB_TIMEOUT_SECONDS = 60 * 60
VERIFY_TIMEOUT_SECONDS = 15 * 60

_lock = threading.Lock()
_threads: dict[str, threading.Thread] = {}


# ── jobs ──────────────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_jobs() -> list[dict]:
    try:
        return json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_job(job: dict) -> None:
    with _lock:
        jobs = [j for j in _read_jobs() if j["id"] != job["id"]]
        JOBS_DIR.mkdir(parents=True, exist_ok=True)
        JOBS_PATH.write_text(json.dumps([job, *jobs], indent=2), encoding="utf-8")


def _update(job: dict, **changes) -> None:
    job.update(changes)
    _save_job(job)


def scenario_paths(pkg: str) -> list[Path]:
    """Everything that belongs to one generated scenario (starters, solutions, tests, copies)."""
    return [
        GEN_STARTERS_DIR / pkg,
        GEN_WEB_STARTERS_DIR / pkg,
        SOLUTIONS_DIR / "gen" / pkg,
        SOLUTIONS_DIR / "gen_web" / pkg,
        REPO_ROOT / "backend" / "tests" / "gen" / pkg,
        REPO_ROOT / "frontend" / "tests" / "gen" / pkg,
        GEN_WORKSPACE_DIR / pkg,
        GEN_WEB_WORKSPACE_DIR / pkg,
        GENERATED_CONFIG_DIR / f"{pkg}.toml",
        GENERATED_CONFIG_DIR / f"{pkg}.draft.toml",
    ]


def _remove_scenario(pkg: str) -> None:
    interview.stop_app_server(pkg)
    for path in scenario_paths(pkg):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    load_catalog.cache_clear()


def _package_name(company: str, domain: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (company or domain or "scenario").lower()).strip("_")[:24] or "scenario"
    taken = {p.name for p in GEN_STARTERS_DIR.glob("*")} | {j["pkg"] for j in _read_jobs()}
    taken |= {c.get("app") for c in interview.load_configs()}
    name, n = f"gen_{base}", 2
    while name in taken:
        name, n = f"gen_{base}_{n}", n + 1
    return name


def _free_port() -> int:
    used = {c.get("api_port") for c in interview.load_configs()} | {j.get("port") for j in _read_jobs()}
    port = FIRST_PORT
    while port in used:
        port += 1
    return port


# ── the generator prompt ──────────────────────────────────────────────────────

DIFFICULTY = {
    "warmup": "WARMUP: two straightforward root causes (one backend, one frontend), solvable in ~12-15 minutes "
    "by a strong engineer with an AI assistant.",
    "standard": "STANDARD: like the stock 60-minute scenarios: ~25 minutes for the bug, a backend and a frontend "
    "root cause, and at least one trap a naive fix misses (a test catches the weak fix).",
    "hard": "HARD: ~35 minutes for the bug, more than one backend layer involved plus a frontend cause, and a "
    "real-world edge case (timezones/DST, idempotency, money rounding, ordering, pagination, stale data...) "
    "that weak fixes miss.",
}


def _prompt(job: dict) -> str:
    pkg, port, minutes = job["pkg"], job["port"], job["minutes"]
    features = 2 if minutes <= 30 else 3
    company = job["company"].strip()
    domain = job["domain"].strip()
    if company:
        who = (
            f"The candidate is preparing for an interview at **{company}**. Base the app on a realistic, small slice "
            f"of {company}'s product and domain (what they actually build, their users, their business rules), using "
            f"what you know about the company. Name the company in the scenario as {company}. Don't invent "
            "anything presented as their real internal systems: it's a plausible practice slice."
        )
        if domain:
            who += f" The candidate adds: {domain}"
    elif domain:
        who = f"Domain: {domain}. Use a fictional company that fits it (not a real company's name)."
    else:
        who = "Pick a realistic product domain yourself and a fictional company (not a real company's name)."

    return f"""You are generating a new scenario for a local mock-interview trainer (repo root: {REPO_ROOT.as_posix()}).

## The format being simulated
A timed AI-assisted coding interview: the candidate works in a browser IDE on an unfamiliar, small
full-stack app (Python FastAPI backend + React/TypeScript frontend) with an AI assistant and a
Claude-played interviewer. First they debug a USER-REPORTED bug (a support ticket in plain words with
concrete numbers); when the bug's tests pass, feature requests unlock and they pick one.

## This scenario
- {who}
- Length: {minutes} minutes. {DIFFICULTY[job["difficulty"]]}
- {features} feature requests, each ~{12 if minutes <= 30 else 20} minutes, distinct from each other, realistic for the
  product, written as a short PM/user request with deliberate ambiguity (the interviewer notes pin down the
  exact tested behavior).

## Study these templates first (copy their structure, conventions and quality bar)
- The 30-minute warmup: backend/interview/warmup.toml, the `ai4` entry in backend/catalog.toml,
  backend/starters/warmup/, backend/starters/warmup_web/, backend/solutions/warmup*/, backend/tests/warmup/,
  frontend/tests/warmup/.
- For richer tickets and interviewer notes: backend/interview/payouts.toml.

## Exact layout (package name `{pkg}`, API port {port})
Write ONLY these paths (everything else is read-only for you and off limits):
1. backend/starters/gen/{pkg}/ : the Python package `{pkg}` (importable as `{pkg}`, e.g. `from {pkg}.data import X`):
   __init__.py, README.md (codebase tour + domain cheat sheet + the business rules the bug violates),
   main.py (FastAPI `app`; register error handlers; add CORSMiddleware with allow_origins
   ["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods/headers ["*"]), data.py (IN-MEMORY demo
   data, no database), errors.py (domain errors -> {{"error": {{"code", "message"}}}}), services/, routers/.
   Money in integer cents. Keep it small: ~250-500 lines of backend.
2. backend/starters/gen_web/{pkg}/ : the React page: index.html (`<div id="root">` and
   `<script type="module" src="./main.tsx"></script>`), main.tsx, an App component, api.ts (calls
   `const API = "http://127.0.0.1:{port}"` directly), small pure helper modules (testable), a .css file.
   TypeScript must compile under `strict`. No new npm packages.
3. backend/solutions/gen/{pkg}/ and backend/solutions/gen_web/{pkg}/ : ONLY the changed files (same relative
   paths), implementing the bug fix AND every feature.
4. backend/tests/gen/{pkg}/ : `test_{pkg}_bug.py` (5-9 tests, including edge cases that catch weak fixes) and
   `test_{pkg}_feature_<feature id>.py` per feature (3-6 tests each). Use FastAPI's TestClient on `{pkg}.main.app`.
   No __init__.py, no conftest name clashes (prefix any helper module with `{pkg}_`).
5. frontend/tests/gen/{pkg}/ : vitest tests for the frontend part of the bug (`*.test.ts`, node environment,
   import helpers via `@gen/{pkg}/<module>`, 2-5 tests).
6. backend/interview/generated/{pkg}.draft.toml : the scenario config (TOML), with these top-level keys first:
   id = "{pkg}", title (the user-visible symptom, NOT the root cause), minutes = {minutes}, order = {job["order"]},
   generated = true, app = "{pkg}", api_port = {port}, portal_path = "/src/gen/{pkg}/index.html",
   portal_title, app_summary (2-3 sentences for the AI assistant), company_context, ticket (ends by listing the
   bug test files: backend/tests/gen/{pkg}/test_{pkg}_bug.py and the frontend test path), interviewer_notes
   (hidden: role, glossary, root causes with the exact arithmetic behind the ticket's numbers, strong vs weak
   fixes, answers to likely questions, strong/weak signals);
   then {features} `[[feature]]` tables (id, title, summary, spec, interviewer_notes, tests = [{{ runner = "pytest",
   path = "backend/tests/gen/{pkg}/test_{pkg}_feature_<id>.py" }}]);
   then an `[exercise]` table (the catalog entry): id = "{pkg}", track = "interview", title (short, ends with
   "({minutes} min)"), minutes = {minutes}, topics, quickref = ["fastapi"], root = "backend/workspace/gen/{pkg}",
   extra_roots = ["frontend/src/gen/{pkg}"], tests = the bug suites (pytest backend file + vitest frontend file),
   requirements (short markdown like the warmup's, with the app URL http://127.0.0.1:5173/src/gen/{pkg}/index.html
   and Swagger http://127.0.0.1:{port}/docs), hints (2-3 progressive hints, none giving the answer).

## Rules
- The bug must be subtle and realistic: no comments or names that give it away, no TODOs.
- Every starter must FAIL the bug suites and every feature suite; the solution must PASS all of them.
- Verify with: `uv run python scripts/verify_solutions.py --only {pkg}` and iterate until it prints
  "All exercises start broken and all reference solutions pass." with lines for `{pkg}` and each `{pkg}:<feature>`.
  Also run `uv run ruff check backend/solutions/gen/{pkg} backend/tests/gen/{pkg}` and fix what it reports.
- Your final reply is just the word DONE. Never describe the bug in your replies: the candidate may see them.
"""


# ── running a job ─────────────────────────────────────────────────────────────


def _rule(tool: str, path: Path) -> str:
    absolute = path.as_posix()
    return f"{tool}({'/' if absolute.startswith('/') else '//'}{absolute}/**)"


def _file_rule(tool: str, path: Path) -> str:
    absolute = path.as_posix()
    return f"{tool}({'/' if absolute.startswith('/') else '//'}{absolute})"


def _claude_args(job: dict) -> list[str]:
    pkg = job["pkg"]
    writable = scenario_paths(pkg)[:6]  # starters, solutions and tests of this package only
    draft = GENERATED_CONFIG_DIR / f"{pkg}.draft.toml"
    allowed = [
        "Read", "Glob", "Grep",
        *[_rule(tool, p) for p in writable for tool in ("Write", "Edit")],
        _file_rule("Write", draft), _file_rule("Edit", draft),
        f"Bash(uv run python scripts/verify_solutions.py --only {pkg})",
        "Bash(uv run pytest:*)",
        "Bash(uv run ruff check:*)",
    ]
    denied = [_rule(tool, DATA_DIR) for tool in ("Read", "Grep", "Glob")]  # your session logs stay private
    return [
        "--permission-mode", "dontAsk",
        "--tools", "Read,Write,Edit,Glob,Grep,Bash",
        "--allowedTools", *allowed,
        "--disallowedTools", *denied,
    ]


def _verify(job: dict, log) -> str | None:
    """Run the content check for this scenario. Returns an error message, or None when it passes."""
    pkg = job["pkg"]
    if not (GENERATED_CONFIG_DIR / f"{pkg}.draft.toml").exists():
        return "The generator didn't write the scenario config."
    try:
        tomllib.loads((GENERATED_CONFIG_DIR / f"{pkg}.draft.toml").read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return f"The scenario config isn't valid TOML: {e}"
    result = subprocess.run(
        [sys.executable, "scripts/verify_solutions.py", "--only", pkg],
        cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=VERIFY_TIMEOUT_SECONDS,
    )
    log.write(f"\n\n===== verify =====\n{result.stdout}\n{result.stderr}\n")
    checked = [line for line in result.stdout.splitlines() if re.match(rf"\s+(ok |XX )\s*{re.escape(pkg)}(:|\s)", line)]
    if result.returncode != 0:
        return "The content check failed (a starter passes or a solution fails)."
    if len(checked) < 4:  # starter + solution, for the bug and at least one feature
        return "The content check didn't find the scenario's tests."
    return None


def _run(job: dict) -> None:
    pkg = job["pkg"]
    command = interview._claude_command()
    log_path = JOBS_DIR / f"{pkg}.log"
    if command is None:
        _update(job, status="failed", error="The `claude` CLI isn't on PATH.", finished_at=_now())
        return
    model = os.environ.get("TRAINER_CLAUDE_MODEL")
    cmd = [
        *command, "-p", "--output-format", "stream-json", "--verbose",
        "--setting-sources", "", "--strict-mcp-config",
        *(["--model", model] if model else []),
        *_claude_args(job),
    ]
    error = None
    with log_path.open("w", encoding="utf-8") as log:
        try:
            proc = subprocess.Popen(
                cmd, cwd=REPO_ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
        except OSError as e:
            _update(job, status="failed", error=f"Could not start claude: {e}", finished_at=_now())
            return
        timer = threading.Timer(JOB_TIMEOUT_SECONDS, proc.kill)
        timer.start()
        try:
            assert proc.stdin is not None and proc.stdout is not None
            proc.stdin.write(_prompt(job))
            proc.stdin.close()
            steps = 0
            for line in proc.stdout:
                log.write(line)
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if msg.get("type") == "assistant":
                    tools = [b.get("name") for b in msg.get("message", {}).get("content", []) if b.get("type") == "tool_use"]
                    if tools:
                        steps += len(tools)
                        _update(job, steps=steps, last_tool=tools[-1])
                elif msg.get("type") == "result":
                    _update(job, cost_usd=msg.get("total_cost_usd"))
            proc.wait()
        finally:
            timer.cancel()
        if proc.returncode != 0:
            error = f"The generator stopped (exit code {proc.returncode}). See {log_path.relative_to(REPO_ROOT)}."
        if error is None:
            _update(job, status="verifying")
            try:
                error = _verify(job, log)
            except subprocess.TimeoutExpired:
                error = "The content check timed out."
    if error:
        _remove_scenario(pkg)
        _update(job, status="failed", error=error, finished_at=_now())
        return
    (GENERATED_CONFIG_DIR / f"{pkg}.draft.toml").rename(GENERATED_CONFIG_DIR / f"{pkg}.toml")
    load_catalog.cache_clear()
    init_workspace()  # create your working copies
    config = tomllib.loads((GENERATED_CONFIG_DIR / f"{pkg}.toml").read_text(encoding="utf-8"))
    _update(job, status="ready", title=config["exercise"]["title"], finished_at=_now())


# ── endpoints ─────────────────────────────────────────────────────────────────


class GenerateBody(BaseModel):
    company: str = Field(default="", max_length=80)  # base the scenario on this company's product/domain
    domain: str = Field(default="", max_length=400)  # optional: what the company does / what to focus on
    minutes: Literal[30, 60] = 60
    difficulty: Literal["warmup", "standard", "hard"] = "standard"


@router.get("")
def list_jobs() -> list[dict]:
    jobs = _read_jobs()
    for job in jobs:  # the trainer restarted while a job was running
        if job["status"] in ("running", "verifying") and job["id"] not in _threads:
            _remove_scenario(job["pkg"])
            _update(job, status="failed", error="Interrupted (the trainer restarted).", finished_at=_now())
    return jobs


@router.post("")
def start_job(body: GenerateBody) -> dict:
    if any(j["status"] in ("running", "verifying") for j in list_jobs()):
        raise HTTPException(status_code=409, detail="A scenario is already being generated")
    if interview._claude_command() is None:
        raise HTTPException(status_code=409, detail="The `claude` CLI isn't on PATH")
    order = 10 + len([c for c in interview.load_configs() if c.get("generated")])
    job = {
        "id": datetime.now(UTC).strftime("%Y%m%d-%H%M%S"),
        "status": "running",
        "company": body.company.strip(),
        "domain": body.domain.strip(),
        "minutes": body.minutes,
        "difficulty": body.difficulty,
        "pkg": _package_name(body.company, body.domain),
        "port": _free_port(),
        "order": order,
        "steps": 0,
        "last_tool": None,
        "title": None,
        "error": None,
        "cost_usd": None,
        "started_at": _now(),
        "finished_at": None,
    }
    _save_job(job)
    thread = threading.Thread(target=_run, args=(job,), daemon=True, name=f"generate-{job['pkg']}")
    _threads[job["id"]] = thread
    thread.start()
    return job


@router.post("/{job_id}/dismiss")
def dismiss(job_id: str) -> dict:
    with _lock:
        jobs = _read_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)
        if job and job["status"] in ("running", "verifying"):
            raise HTTPException(status_code=409, detail="Still generating")
        JOBS_PATH.write_text(json.dumps([j for j in jobs if j["id"] != job_id], indent=2), encoding="utf-8")
    return {"ok": True}


@router.delete("/scenario/{pkg}")
def delete_scenario(pkg: str) -> dict:
    """Delete a generated scenario (its files; your past session logs stay)."""
    config = next((c for c in interview.load_configs() if c.get("generated") and c.get("app") == pkg), None)
    if config is None:
        raise HTTPException(status_code=404, detail=f"No generated scenario {pkg}")
    state = interview._read_state(False)
    if state and state.get("exercise") == config["id"] and not state.get("ended_at"):
        raise HTTPException(status_code=409, detail="End the interview on this scenario first")
    _remove_scenario(pkg)
    return {"ok": True}
