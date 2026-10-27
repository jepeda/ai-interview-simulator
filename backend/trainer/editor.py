"""Backend for the in-browser editor: file read/write, Python IntelliSense (Jedi) and lint (Ruff).

Jedi runs inside the trainer's own interpreter (the project's .venv), so completions know about
fastapi, sqlalchemy, pydantic and the exercise packages exactly as the tests will see them.
"""

import json
import subprocess
import sys
import threading
from pathlib import Path

import jedi
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from trainer import interview
from trainer.catalog import load_catalog, roots_of
from trainer.paths import BACKEND_DIR, REPO_ROOT, WORKSPACE_DIR

router = APIRouter(prefix="/api/editor", tags=["editor"])

_jedi_lock = threading.Lock()  # Jedi's caches are not thread-safe
_project = jedi.Project(
    path=REPO_ROOT,
    added_sys_path=[str(WORKSPACE_DIR), str(BACKEND_DIR)],
    smart_sys_path=False,
)

# Extra read-only files the editor may load (types the dbg5 TypeScript file imports).
EXTRA_READ_ONLY = {"frontend/src/clinic/types.ts"}


TREE_SUFFIXES = {".py", ".ts", ".tsx", ".css", ".md", ".toml", ".json", ".txt"}

# Every exercise gets a generated, read-only REQUIREMENTS.md pinned at the top of its file tree,
# so the brief is inside the IDE (and in full-screen mode). It isn't a file on disk.
REQUIREMENTS_PREFIX = ".trainer/"
TRACK_LABELS = {"syntax": "Syntax drill", "debugging": "Debugging challenge", "project": "Interview project"}


def requirements_path(exercise_id: str) -> str:
    return f"{REQUIREMENTS_PREFIX}{exercise_id}/REQUIREMENTS.md"


def _requirements_exercise(path: str) -> str | None:
    """`.trainer/py01/REQUIREMENTS.md` -> "py01" (None for real files)."""
    parts = path.split("/")
    if len(parts) == 3 and path.startswith(REQUIREMENTS_PREFIX) and parts[2] == "REQUIREMENTS.md":
        return parts[1]
    return None


def _requirements_markdown(ex) -> str:
    files = "\n".join(f"- `{f}`" for f in ex.files) if not ex.root else f"- everything under `{ex.root}/`"
    tests = "\n".join(f"- `{t.path}`" for t in ex.tests)
    return (
        f"# {ex.id} · {ex.title}\n\n"
        f"**{TRACK_LABELS.get(ex.track, ex.track)}** · ~{ex.minutes} min · {', '.join(ex.topics)}\n\n"
        f"{ex.requirements.strip()}\n\n"
        "---\n\n"
        f"**You edit:**\n{files}\n\n"
        f"**Tests (read-only):**\n{tests}\n\n"
        "**Ctrl/⌘+Enter** saves and runs the tests. Hints are in the panel next to the editor.\n"
    )


def _root_files(root: str) -> list[str]:
    """Files currently on disk under an exercise root (includes files you created)."""
    base = REPO_ROOT / root
    if not base.is_dir():
        return []
    return sorted(
        f.relative_to(REPO_ROOT).as_posix()
        for f in base.rglob("*")
        if f.is_file() and f.suffix in TREE_SUFFIXES and "__pycache__" not in f.parts
    )


def _editable_paths() -> set[str]:
    catalog = load_catalog().values()
    roots = {r for ex in catalog for r in roots_of(ex)}
    return {f for ex in catalog for f in ex.files} | {f for r in roots for f in _root_files(r)}


def _readable_paths() -> set[str]:
    tests = {t.path for ex in load_catalog().values() for t in ex.tests}
    return _editable_paths() | tests | EXTRA_READ_ONLY | interview.feature_test_paths()


def _resolve(path: str, allowed: set[str]) -> Path:
    if path not in allowed:
        raise HTTPException(status_code=403, detail=f"{path} is not an exercise file")
    return REPO_ROOT / path


def _language(path: str) -> str:
    suffix = Path(path).suffix
    return {".ts": "typescript", ".tsx": "typescript", ".css": "css", ".md": "markdown", ".toml": "ini", ".json": "json"}.get(
        suffix, "python"
    )


# ── files ──────────────────────────────────────────────────────────────────────


@router.get("/tree")
def tree(exercise: str) -> dict:
    """Every file the editor should list for an exercise: its root folder, its own files, its tests."""
    ex = load_catalog().get(exercise)
    if ex is None:
        raise HTTPException(status_code=404, detail=f"Unknown exercise {exercise}")
    editable = set(ex.files) | {f for r in roots_of(ex) for f in _root_files(r)}
    tests = {t.path for t in ex.tests} | set(interview.unlocked_tests(ex.id))
    files = [{"path": requirements_path(ex.id), "read_only": True, "pinned": True}]
    files += [{"path": p, "read_only": False} for p in sorted(editable)]
    files += [{"path": p, "read_only": True} for p in sorted(tests)]
    return {"root": ex.root, "files": files}


@router.get("/file")
def read_file(path: str) -> dict:
    if (exercise_id := _requirements_exercise(path)) is not None:
        ex = load_catalog().get(exercise_id)
        if ex is None:
            raise HTTPException(status_code=404, detail=f"Unknown exercise {exercise_id}")
        return {"path": path, "content": _requirements_markdown(ex), "language": "markdown", "read_only": True, "mtime": 0}
    file = _resolve(path, _readable_paths())
    if not file.exists():
        raise HTTPException(status_code=404, detail=f"{path} does not exist; run setup")
    # newline="" keeps the file's own line endings (CRLF on Windows checkouts stays CRLF).
    with file.open(encoding="utf-8", newline="") as f:
        content = f.read()
    return {
        "path": path,
        "content": content,
        "language": _language(path),
        "read_only": path not in _editable_paths(),
        "mtime": file.stat().st_mtime,
    }


class SaveBody(BaseModel):
    path: str
    content: str


@router.put("/file")
def save_file(body: SaveBody) -> dict:
    file = _resolve(body.path, _editable_paths())
    try:
        before = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        before = None
    with file.open("w", encoding="utf-8", newline="") as f:
        f.write(body.content)
    interview.record_manual_save(body.path, before, body.content)  # mock interview: your edit
    return {"path": body.path, "mtime": file.stat().st_mtime}


# ── Python IntelliSense ───────────────────────────────────────────────────────


class CodeBody(BaseModel):
    path: str
    content: str
    line: int = 1  # 1-based (Monaco and Jedi agree)
    column: int = 1  # 1-based from Monaco; Jedi wants 0-based


def _script(body: CodeBody) -> jedi.Script:
    if body.path not in _readable_paths() or not body.path.endswith(".py"):
        raise HTTPException(status_code=403, detail="Not a Python exercise file")
    return jedi.Script(code=body.content, path=REPO_ROOT / body.path, project=_project)


def _clamp(body: CodeBody) -> tuple[int, int]:
    lines = body.content.splitlines() or [""]
    line = min(max(body.line, 1), len(lines))
    column = min(max(body.column - 1, 0), len(lines[line - 1]))
    return line, column


@router.post("/complete")
def complete(body: CodeBody) -> dict:
    line, column = _clamp(body)
    with _jedi_lock:
        completions = _script(body).complete(line, column)[:200]
        items = [
            {
                "label": c.name,
                "kind": c.type,  # module, class, instance, function, param, path, keyword, property, statement
                "detail": c.description,
                "insert": c.name,
                "prefix_len": len(c.name) - len(c.complete or ""),
            }
            for c in completions
        ]
    return {"items": items}


@router.post("/hover")
def hover(body: CodeBody) -> dict:
    line, column = _clamp(body)
    with _jedi_lock:
        names = _script(body).help(line, column)
        if not names:
            return {"contents": None}
        name = names[0]
        signatures = [s.to_string() for s in name.get_signatures()][:3]
        doc = name.docstring(raw=True).strip()
        header = "\n".join(signatures) if signatures else f"{name.type} {name.full_name or name.name}"
    contents = f"```python\n{header}\n```"
    if doc:
        contents += "\n\n" + doc[:2000]
    return {"contents": contents}


@router.post("/signature")
def signature(body: CodeBody) -> dict:
    line, column = _clamp(body)
    with _jedi_lock:
        sigs = _script(body).get_signatures(line, column)
        result = [
            {
                "label": s.to_string(),
                "doc": s.docstring(raw=True).strip()[:1500],
                "params": [p.to_string() for p in s.params],
                "active_param": s.index,
            }
            for s in sigs[:3]
        ]
    return {"signatures": result}


@router.post("/definition")
def definition(body: CodeBody) -> dict:
    line, column = _clamp(body)
    with _jedi_lock:
        targets = []
        for d in _script(body).goto(line, column, follow_imports=True):
            if d.module_path is None or d.line is None:
                continue
            try:
                rel = Path(d.module_path).resolve().relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = None  # library code outside the repo
            targets.append({"path": rel, "line": d.line, "column": d.column + 1, "description": d.description})
    return {"targets": targets}


# ── diagnostics ───────────────────────────────────────────────────────────────


class LintBody(BaseModel):
    path: str
    content: str


@router.post("/lint")
def lint(body: LintBody) -> dict:
    """Syntax errors from Jedi/parso + Ruff findings (undefined names, unused imports, ...)."""
    if body.path not in _readable_paths() or not body.path.endswith(".py"):
        return {"diagnostics": []}
    diagnostics: list[dict] = []
    with _jedi_lock:
        for err in jedi.Script(code=body.content, path=REPO_ROOT / body.path, project=_project).get_syntax_errors():
            diagnostics.append({
                "line": err.line, "column": err.column + 1,
                "end_line": err.until_line, "end_column": err.until_column + 1,
                "message": err.get_message(), "severity": "error", "code": "syntax",
            })
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format", "json", "--no-cache",
         "--stdin-filename", body.path, "-"],
        input=body.content, capture_output=True, text=True, encoding="utf-8",
        cwd=REPO_ROOT, timeout=20, check=False,
    )
    try:
        findings = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        findings = []
    for f in findings:
        if f.get("code") in (None, "invalid-syntax"):  # ruff's syntax errors duplicate Jedi's
            continue
        diagnostics.append({
            "line": f["location"]["row"], "column": f["location"]["column"],
            "end_line": f["end_location"]["row"], "end_column": f["end_location"]["column"],
            "message": f["message"], "severity": "error" if f["code"].startswith("F8") else "warning",
            "code": f["code"],
        })
    return {"diagnostics": diagnostics}


def warm_up() -> None:
    """Import-heavy libraries take a second to index on first use; do it at startup."""
    with _jedi_lock:
        jedi.Script("import fastapi, sqlalchemy, pydantic\nfastapi.", project=_project).complete(2, 8)

