"""The dashboard API (trainer/main.py) and progress tracking, with a throwaway progress DB and
settings file, and test runs / resets faked."""

import pytest

from trainer import main


@pytest.fixture
def api(client, runner, monkeypatch):
    monkeypatch.setattr(main, "run_exercise", runner)
    resets: list[list[str]] = []
    monkeypatch.setattr(main, "reset_files", lambda files: resets.append(files) or [])
    client.resets = resets
    return client


# ── settings / countdown ──────────────────────────────────────────────────────


def test_interview_date_is_unset_until_you_pick_one(api):
    assert api.get("/api/meta").json()["interview_date"] is None


def test_interview_date_can_be_set_changed_and_cleared(api):
    assert api.put("/api/settings", json={"interview_date": "2026-11-03"}).json() == {"interview_date": "2026-11-03"}
    assert api.get("/api/meta").json()["interview_date"] == "2026-11-03"
    api.put("/api/settings", json={"interview_date": "2026-11-10"})
    assert api.get("/api/meta").json()["interview_date"] == "2026-11-10"
    api.put("/api/settings", json={"interview_date": None})
    assert api.get("/api/meta").json()["interview_date"] is None


def test_an_invalid_date_is_rejected(api):
    assert api.put("/api/settings", json={"interview_date": "next tuesday"}).status_code == 422
    assert api.put("/api/settings", json={"interview_date": "2026-02-30"}).status_code == 422


def test_settings_live_in_the_gitignored_data_folder():
    assert main.SETTINGS_PATH.name == "settings.json"
    assert "backend/data/" in (main.REPO_ROOT / ".gitignore").read_text()


# ── exercises & progress ──────────────────────────────────────────────────────


def test_the_exercise_list_starts_not_started(api):
    exercises = api.get("/api/exercises").json()
    ids = [e["id"] for e in exercises]
    assert {"py01", "dbg1", "proj1", "ai0", "ai1", "ai2", "ai3", "ai4"} <= set(ids)
    assert all(e["status"] == "not_started" and e["last_total"] is None for e in exercises)


def test_unknown_exercise_is_404(api):
    assert api.get("/api/exercises/nope").status_code == 404
    assert api.post("/api/exercises/nope/run").status_code == 404


def test_a_failing_run_marks_it_in_progress_and_a_passing_run_completes_it(api, runner):
    suite = api.get("/api/exercises/py01").json()["tests"][0]["path"]
    runner.failing = {suite}
    detail = api.post("/api/exercises/py01/run").json()
    assert detail["status"] == "in_progress" and detail["attempts"] == 1 and detail["last_result"]["ok"] is False
    runner.failing = set()
    detail = api.post("/api/exercises/py01/run").json()
    assert detail["status"] == "completed" and detail["times_completed"] == 1 and detail["attempts"] == 2
    detail = api.post("/api/exercises/py01/run").json()
    assert detail["times_completed"] == 1  # passing again doesn't count twice


def test_hints_are_revealed_one_at_a_time_and_stop_at_the_last(api):
    total = api.get("/api/exercises/py01").json()["hints_total"]
    for n in range(1, total + 2):
        detail = api.post("/api/exercises/py01/hint").json()
        assert len(detail["hints"]) == min(n, total)
    assert detail["status"] == "in_progress"


def test_manual_complete_and_uncomplete(api):
    assert api.post("/api/exercises/py02/complete", json={"completed": True}).json()["status"] == "completed"
    detail = api.post("/api/exercises/py02/complete", json={"completed": False}).json()
    assert detail["status"] == "in_progress" and detail["times_completed"] == 1  # history kept


def test_reset_restores_the_files_and_clears_progress_but_keeps_history(api):
    api.post("/api/exercises/py03/complete", json={"completed": True})
    api.post("/api/exercises/py03/hint")
    detail = api.post("/api/exercises/py03/reset").json()
    assert detail["status"] == "not_started" and detail["hints"] == [] and detail["attempts"] == 0
    assert detail["times_completed"] == 1
    assert api.resets == [[f["path"] for f in detail["files"]]]


def test_exercise_detail_lists_files_tests_and_quickref(api):
    detail = api.get("/api/exercises/proj1").json()
    assert detail["files"] and all(f["path"].startswith("backend/workspace/booking/") for f in detail["files"])
    assert {t["runner"] for t in detail["tests"]} == {"pytest"}
    assert detail["quickref"] and detail["hints"] == []


# ── docs ──────────────────────────────────────────────────────────────────────


def test_cheatsheet_and_quickref_pages_load(api):
    assert api.get("/api/cheatsheet").json()["markdown"].strip()
    pages = api.get("/api/quickref").json()
    assert pages and all(p["id"] and p["title"] and p["markdown"] for p in pages)


def test_opening_a_non_exercise_file_in_an_ide_is_refused(api):
    res = api.post("/api/open", json={"path": "backend/trainer/main.py", "editor": "vscode"})
    assert res.status_code == 400
