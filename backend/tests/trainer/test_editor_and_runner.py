"""The browser editor's file API, the test runner's result parsing, and the starter <-> working-copy
mapping."""

from pathlib import Path

import pytest

from trainer import editor, interview
from trainer.catalog import TestSuite as Suite
from trainer.paths import REPO_ROOT, STARTERS_DIR
from trainer.runner import _suite_of, _summary_line
from trainer.workspace import starter_for

# ── editor ────────────────────────────────────────────────────────────────────


def test_requirements_are_a_virtual_read_only_markdown_file(client):
    path = editor.requirements_path("ai4")
    assert path == ".trainer/ai4/REQUIREMENTS.md" and editor._requirements_exercise(path) == "ai4"
    assert editor._requirements_exercise("backend/workspace/x.py") is None
    res = client.get("/api/editor/file", params={"path": path}).json()
    assert res["read_only"] and res["language"] == "markdown" and res["content"].startswith("# ai4 · ")


@pytest.mark.parametrize(
    ("path", "language"),
    [("a.py", "python"), ("a.ts", "typescript"), ("a.tsx", "typescript"), ("a.css", "css"), ("README.md", "markdown"), ("x.json", "json")],
)
def test_language_from_extension(path, language):
    assert editor._language(path) == language


def test_files_outside_the_exercises_are_off_limits(client):
    assert client.get("/api/editor/file", params={"path": "backend/trainer/main.py"}).status_code == 403
    assert client.get("/api/editor/file", params={"path": "backend/solutions/warmup/money.py"}).status_code == 403
    assert client.put("/api/editor/file", json={"path": "backend/trainer/main.py", "content": "x"}).status_code == 403


def test_tests_are_readable_but_not_editable(client):
    res = client.get("/api/editor/file", params={"path": "backend/tests/warmup/test_bug_balances.py"}).json()
    assert res["read_only"] is True and res["language"] == "python"


def test_the_tree_pins_requirements_and_lists_code_then_tests(client):
    files = client.get("/api/editor/tree", params={"exercise": "ai4"}).json()["files"]
    assert files[0] == {"path": ".trainer/ai4/REQUIREMENTS.md", "read_only": True, "pinned": True}
    editable = [f["path"] for f in files if not f["read_only"]]
    assert "backend/workspace/warmup/money.py" in editable and "frontend/src/warmup/balances.ts" in editable
    assert [f["path"] for f in files if f["read_only"] and not f.get("pinned")] == sorted(t.path for t in interview._exercise(interview.load_config("ai4")).tests)
    assert client.get("/api/editor/tree", params={"exercise": "nope"}).status_code == 404


def test_the_tree_shows_feature_tests_once_a_feature_is_chosen(client):
    client.post("/api/interview/start", json={"scenario": "ai4"})
    client.post("/api/interview/run")
    client.post("/api/interview/feature", json={"feature_id": "minimum"})
    paths = [f["path"] for f in client.get("/api/editor/tree", params={"exercise": "ai4"}).json()["files"]]
    assert "backend/tests/warmup/test_feature_minimum.py" in paths
    assert "backend/tests/warmup/test_feature_aging.py" not in paths


def test_saving_writes_the_file_and_reports_it_to_the_interview(client, tmp_path, monkeypatch):
    rel = "backend/workspace/warmup/money.py"
    monkeypatch.setattr(editor, "REPO_ROOT", tmp_path)  # write into a temp copy, not your workspace
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).write_text("old\n")
    saves = []
    monkeypatch.setattr(interview, "record_manual_save", lambda *args: saves.append(args))
    assert client.put("/api/editor/file", json={"path": rel, "content": "new\n"}).status_code == 200
    assert (tmp_path / rel).read_text() == "new\n"
    assert saves == [(rel, "old\n", "new\n")]


# ── runner ────────────────────────────────────────────────────────────────────


def test_summary_line_prefers_the_message_then_the_last_assertion():
    assert _summary_line("AssertionError: 1 != 2\nmore", "") == "AssertionError: 1 != 2"
    details = "def test():\n>   assert x\nE   assert 2666 == 2667\nE    +  where 2666 = f()\nfile.py:3: AssertionError"
    assert _summary_line("collection failure", details) == "+  where 2666 = f()"
    assert _summary_line("", "line one\nlast line") == "last line"
    assert len(_summary_line("x" * 1000, "")) == 300


def test_suite_of_maps_a_module_back_to_its_suite():
    suites = [Suite("pytest", "backend/tests/booking/test_p1.py"), Suite("pytest", "backend/tests/booking/test_p2.py")]
    assert _suite_of("backend.tests.booking.test_p2", suites) == "backend/tests/booking/test_p2.py"
    assert _suite_of("somewhere.else", suites) == suites[0].path


# ── starters <-> working copies ───────────────────────────────────────────────


@pytest.mark.parametrize(
    ("work", "starter"),
    [
        ("backend/workspace/drills/ex01_dicts.py", "drills/ex01_dicts.py"),
        ("backend/workspace/payouts/services/periods.py", "payouts/services/periods.py"),
        ("frontend/src/payouts/format.ts", "payouts_web/format.ts"),
        ("frontend/src/clinic/patientState.ts", "frontend/patientState.ts"),
        ("backend/workspace/gen/gen_acme/main.py", "gen/gen_acme/main.py"),
        ("frontend/src/gen/gen_acme/api.ts", "gen_web/gen_acme/api.ts"),
    ],
)
def test_starter_for_maps_working_copies_to_starters(work, starter):
    assert starter_for(work) == STARTERS_DIR / starter


def test_starter_for_rejects_non_exercise_files():
    with pytest.raises(ValueError):
        starter_for("backend/trainer/main.py")


def test_repo_root_is_the_project_folder():
    assert (REPO_ROOT / "backend" / "catalog.toml").is_file() and isinstance(REPO_ROOT, Path)
