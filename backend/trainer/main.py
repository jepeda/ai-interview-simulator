"""Trainer API: serves the dashboard (exercise catalog, test runs, hints, progress).

This is infrastructure, not an exercise -- you don't need to edit anything here.
"""

import json
import shutil
import subprocess
import sys
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from trainer import editor, interview, progress
from trainer.catalog import Exercise, load_catalog
from trainer.paths import CHEATSHEET_PATH, DATA_DIR, QUICKREF_DIR, REPO_ROOT
from trainer.runner import run_exercise
from trainer.workspace import init_workspace, is_modified, reset_files

# Personal settings (e.g. your interview date for the countdown). Lives in backend/data, which is
# gitignored, so it never ends up in the repo.
SETTINGS_PATH = DATA_DIR / "settings.json"


def _read_settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_workspace()  # recreate any missing working copies (never overwrites your edits)
    threading.Thread(target=editor.warm_up, daemon=True).start()
    yield


app = FastAPI(title="Python Interview Trainer", lifespan=lifespan)
app.include_router(editor.router)
app.include_router(interview.router)


def _get_exercise(exercise_id: str) -> Exercise:
    exercise = load_catalog().get(exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail=f"Unknown exercise {exercise_id}")
    return exercise


def _summary(ex: Exercise, prog: dict) -> dict:
    last = prog.get("last_result")
    return {
        "id": ex.id,
        "track": ex.track,
        "title": ex.title,
        "minutes": ex.minutes,
        "topics": ex.topics,
        "status": prog["status"],
        "last_passed": last["passed"] if last else None,
        "last_total": last["total"] if last else None,
    }


def _detail(ex: Exercise) -> dict:
    prog = progress.get(ex.id)
    revealed = prog["hints_revealed"]
    return {
        **_summary(ex, prog),
        "requirements": ex.requirements,
        "files": [
            {"path": f, "abs_path": str(REPO_ROOT / f), "modified": is_modified(f)} for f in ex.files
        ],
        "tests": [
            {"runner": t.runner, "path": t.path, "abs_path": str(REPO_ROOT / t.path)} for t in ex.tests
        ],
        "hints_total": len(ex.hints),
        "quickref": ex.quickref,
        "hints": ex.hints[:revealed],
        "attempts": prog["attempts"],
        "times_completed": prog["times_completed"],
        "completed_at": prog["completed_at"],
        "last_result": prog["last_result"],
    }


@app.get("/api/meta")
def meta() -> dict:
    return {
        "interview_date": _read_settings().get("interview_date"),
        "repo_root": str(REPO_ROOT),
        "editors": available_editors(),
    }


class SettingsBody(BaseModel):
    interview_date: date | None = None  # null clears the countdown


@app.put("/api/settings")
def save_settings(body: SettingsBody) -> dict:
    settings = _read_settings()
    settings["interview_date"] = body.interview_date.isoformat() if body.interview_date else None
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings


@app.get("/api/exercises")
def list_exercises() -> list[dict]:
    all_progress = progress.get_all()
    return [
        _summary(ex, all_progress.get(ex.id) or progress.get(ex.id))
        for ex in load_catalog().values()
    ]


@app.get("/api/exercises/{exercise_id}")
def get_exercise(exercise_id: str) -> dict:
    return _detail(_get_exercise(exercise_id))


@app.post("/api/exercises/{exercise_id}/run")
def run_tests(exercise_id: str) -> dict:
    ex = _get_exercise(exercise_id)
    result = run_exercise(ex)
    progress.record_run(ex.id, result)
    return _detail(ex)


@app.post("/api/exercises/{exercise_id}/hint")
def next_hint(exercise_id: str) -> dict:
    ex = _get_exercise(exercise_id)
    progress.reveal_hint(ex.id, len(ex.hints))
    return _detail(ex)


class CompleteBody(BaseModel):
    completed: bool


@app.post("/api/exercises/{exercise_id}/complete")
def mark_complete(exercise_id: str, body: CompleteBody) -> dict:
    ex = _get_exercise(exercise_id)
    progress.set_completed(ex.id, body.completed)
    return _detail(ex)


@app.post("/api/exercises/{exercise_id}/reset")
def reset_exercise(exercise_id: str) -> dict:
    ex = _get_exercise(exercise_id)
    reset_files(ex.files)
    progress.reset(ex.id)
    return _detail(ex)


EditorId = Literal["vscode", "webstorm", "pycharm"]
EDITOR_LABELS: dict[str, str] = {"vscode": "VS Code", "webstorm": "WebStorm", "pycharm": "PyCharm"}
MAC_APPS = {"vscode": "Visual Studio Code", "webstorm": "WebStorm", "pycharm": "PyCharm"}


def _editor_command(editor: str, file: Path) -> list[str] | None:
    """Command that opens `file` in the editor, or None if the editor can't be found."""
    if editor == "vscode":
        code = shutil.which("code")
        if code:
            return [code, "--reuse-window", str(REPO_ROOT), "--goto", str(file)]
    else:
        # JetBrains launchers: enable them in Toolbox (Settings -> Tools -> Shell scripts).
        for name in (editor, f"{editor}64", f"{editor}64.exe", f"{editor}.cmd", f"{editor}.bat"):
            launcher = shutil.which(name)
            if launcher:
                return [launcher, str(REPO_ROOT), str(file)]
    if sys.platform == "darwin" and Path(f"/Applications/{MAC_APPS[editor]}.app").exists():
        return ["open", "-a", MAC_APPS[editor], str(file)]
    return None


def available_editors() -> list[dict]:
    probe = REPO_ROOT / "README.md"
    return [
        {"id": e, "label": EDITOR_LABELS[e], "available": _editor_command(e, probe) is not None}
        for e in EDITOR_LABELS
    ]


class OpenBody(BaseModel):
    path: str
    editor: EditorId = "vscode"


@app.post("/api/open")
def open_in_editor(body: OpenBody) -> dict:
    allowed = {f for ex in load_catalog().values() for f in ex.files}
    allowed |= {t.path for ex in load_catalog().values() for t in ex.tests}
    allowed.add("docs/ts-to-python.md")
    if body.path not in allowed:
        raise HTTPException(status_code=400, detail="Only exercise and test files can be opened")
    label = EDITOR_LABELS[body.editor]
    command = _editor_command(body.editor, REPO_ROOT / body.path)
    if command is None:
        hint = (
            "In VS Code run 'Shell Command: Install code command in PATH' (macOS) or reinstall with "
            "'Add to PATH' checked (Windows)"
            if body.editor == "vscode"
            else "In JetBrains Toolbox enable Settings -> Tools -> Shell scripts, or add the IDE's bin folder to PATH"
        )
        return {"opened": False, "message": f"Couldn't find {label}. {hint}, then restart the dev servers."}
    subprocess.Popen(command, cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"opened": True, "message": f"Opened {body.path} in {label}"}


@app.get("/api/cheatsheet")
def cheatsheet() -> dict:
    return {"markdown": CHEATSHEET_PATH.read_text(encoding="utf-8")}


@app.get("/api/quickref")
def quickref() -> list[dict]:
    """Short reference pages (docs/quickref/*.md); the first line is the `# Title`."""
    pages = []
    for path in sorted(QUICKREF_DIR.glob("*.md")):
        title, _, body = path.read_text(encoding="utf-8").partition("\n")
        pages.append({"id": path.stem, "title": title.removeprefix("# ").strip(), "markdown": body.strip()})
    return pages
