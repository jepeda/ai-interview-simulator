"""Fixtures for the trainer's own tests.

Everything that would touch your real data or code is redirected or faked: session logs, progress,
settings and generator jobs go to a temp folder; resetting the codebase/demo data, starting app
servers, running exercise tests and calling Claude are replaced with fakes. Nothing here touches
backend/workspace or backend/data.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from trainer import generate, interview, main, progress


class FakeClock:
    """Stands in for interview._now so elapsed times and pauses are exact."""

    def __init__(self) -> None:
        self.now = datetime(2026, 10, 26, 15, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


class FakeRunner:
    """Stands in for run_exercise: every case passes unless its suite is listed in `failing`."""

    def __init__(self) -> None:
        self.failing: set[str] = set()
        self.calls: list[list[str]] = []

    def __call__(self, exercise) -> dict:
        suites = [t.path for t in exercise.tests]
        self.calls.append(suites)
        cases = [
            {"suite": s, "name": f"test_{i}", "status": "failed" if s in self.failing else "passed", "message": "", "details": ""}
            for s in suites
            for i in range(2)
        ]
        passed = sum(c["status"] == "passed" for c in cases)
        return {"ok": passed == len(cases), "passed": passed, "failed": len(cases) - passed, "total": len(cases), "cases": cases, "output": ""}


class FakeCode:
    """Stands in for interview._code_files: the 'files on disk' of the interview's app."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {"backend/workspace/app/service.py": "def total():\n    return 1\n"}

    def __call__(self, ex) -> dict[str, str]:
        return dict(self.files)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(interview, "_now", fake)
    return fake


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> FakeRunner:
    fake = FakeRunner()
    monkeypatch.setattr(interview, "run_exercise", fake)
    return fake


@pytest.fixture
def code(monkeypatch: pytest.MonkeyPatch) -> FakeCode:
    fake = FakeCode()
    monkeypatch.setattr(interview, "_code_files", fake)
    return fake


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway backend/data: sessions, progress, settings and generator jobs live here."""
    sessions = tmp_path / "interview"
    monkeypatch.setattr(interview, "SESSIONS_DIR", sessions)
    monkeypatch.setattr(interview, "STATE_PATH", sessions / "current.json")
    monkeypatch.setattr(interview, "SANDBOX_STATE_PATH", sessions / "sandbox.json")
    monkeypatch.setattr(progress, "DB_PATH", tmp_path / "progress.db")
    monkeypatch.setattr(main, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(generate, "JOBS_DIR", tmp_path / "generate")
    monkeypatch.setattr(generate, "JOBS_PATH", tmp_path / "generate" / "jobs.json")
    return tmp_path


@pytest.fixture
def client(data_dir: Path, clock: FakeClock, runner: FakeRunner, code: FakeCode, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """The trainer API with every side effect faked (no lifespan: no workspace init, no Jedi)."""
    monkeypatch.setattr(interview, "_reset_codebase", lambda ex: None)
    monkeypatch.setattr(interview, "_reset_demo_data", lambda cfg: None)
    monkeypatch.setattr(interview, "ensure_app_server", lambda cfg: None)
    monkeypatch.setattr(interview, "_diff", lambda ex: "")
    monkeypatch.setattr(interview, "_procs", {})
    yield TestClient(main.app)

