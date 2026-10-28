"""Make your working copies importable.

Exercises live in backend/workspace (created from backend/starters by setup).
TRAINER_WORKSPACE overrides the location; scripts/verify_solutions.py uses that to
test the reference solutions in a temporary copy.
"""

import os
import sys
import types
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = Path(os.environ.get("TRAINER_WORKSPACE", BACKEND_DIR / "workspace")).resolve()

if not (WORKSPACE_DIR / "drills").is_dir():
    raise pytest.UsageError(
        f"Exercise workspace not found at {WORKSPACE_DIR}. Run setup first (setup.cmd / ./setup.sh)."
    )

sys.path.insert(0, str(WORKSPACE_DIR))
sys.path.insert(0, str(WORKSPACE_DIR / "gen"))  # generated interview scenarios (gen_* packages)

REPO_DIR = BACKEND_DIR.parent


def _is_project_frame(path: object) -> bool:
    """Your code and the tests -- not installed libraries (.venv) or the standard library."""
    raw = str(path)
    if raw.startswith("<"):  # generated code, e.g. "<sqlalchemy generated wrapper>"
        return False
    resolved = Path(raw).resolve()
    if not (resolved.is_relative_to(REPO_DIR) or resolved.is_relative_to(WORKSPACE_DIR)):
        return False
    return ".venv" not in resolved.parts and "site-packages" not in resolved.parts


def _just_my_frames(tb: types.TracebackType) -> types.TracebackType:
    """Rebuild a traceback keeping only project frames (or the last frame, if none are ours)."""
    frames = []
    while tb is not None:
        frames.append(tb)
        tb = tb.tb_next
    keep = [t for t in frames if _is_project_frame(t.tb_frame.f_code.co_filename)] or frames[-1:]
    rebuilt = None
    for t in reversed(keep):
        rebuilt = types.TracebackType(rebuilt, t.tb_frame, t.tb_lasti, t.tb_lineno)
    return rebuilt


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """"Just my code" tracebacks: drop library frames (FastAPI, Starlette, anyio, SQLAlchemy...).

    Keeps failures readable, and fast: pytest re-parses the source of every frame it prints, and
    framework stacks are deep. Exception messages are unchanged. Applied to every exception in the
    chain (`raise ... from ...` and implicit context), since pytest prints each of them.
    """
    excinfo = call.excinfo
    if excinfo is not None and excinfo.value.__traceback__ is not None:
        seen: set[int] = set()
        exc: BaseException | None = excinfo.value
        while exc is not None and id(exc) not in seen:
            seen.add(id(exc))
            if exc.__traceback__ is not None:
                exc.__traceback__ = _just_my_frames(exc.__traceback__)
            exc = exc.__cause__ or exc.__context__
        # Rebuild from the exception itself: pytest re-walks the *raw* traceback (tb_next links),
        # so filtering only its Traceback wrapper would be undone.
        call.excinfo = pytest.ExceptionInfo.from_exception(excinfo.value)
    return (yield)
