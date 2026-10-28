"""What the interview engine records: who changed the code (you vs. the AI), grade parsing, attention
summaries, elapsed time with pauses, and the log the grader reads."""

from datetime import timedelta

import pytest
from trainer_testkit import events

from trainer import interview

FILE = "backend/workspace/app/service.py"


@pytest.fixture
def session(client) -> dict:
    """A running warmup interview (with the code snapshot taken at the start)."""
    client.post("/api/interview/start", json={"scenario": "ai4"})
    return interview._read_state()


def changes(session_id: str) -> list[tuple[str, list[dict]]]:
    return [(e["source"], e["files"]) for e in events(session_id) if e["kind"] == "code_change"]


# ── you vs. the AI ────────────────────────────────────────────────────────────


def test_changes_counts_added_and_removed_lines_per_file():
    files, diff = interview._changes({"a.py": "x\ny\n", "gone.py": "1\n"}, {"a.py": "x\nz\nw\n", "new.py": "n\n"})
    assert files == [
        {"path": "a.py", "added": 2, "removed": 1},
        {"path": "gone.py", "added": 0, "removed": 1},
        {"path": "new.py", "added": 1, "removed": 0},
    ]
    assert "+z" in "".join(diff) and "-y" in "".join(diff)


def test_a_checkpoint_logs_what_changed_since_the_last_one(session, code):
    code.files[FILE] += "# mine\n"
    interview._attribute(session, "manual")
    code.files[FILE] += "# ai 1\n# ai 2\n"
    interview._attribute(session, "ai")
    interview._attribute(session, "manual")  # nothing new: no event
    assert changes(session["session_id"]) == [
        ("manual", [{"path": FILE, "added": 1, "removed": 0}]),
        ("ai", [{"path": FILE, "added": 2, "removed": 0}]),
    ]


def test_an_editor_save_is_logged_as_exactly_what_that_save_changed(session, code):
    before = code.files[FILE]
    code.files[FILE] = before + "# saved\n"
    interview.record_manual_save(FILE, before, code.files[FILE])
    assert changes(session["session_id"]) == [("manual", [{"path": FILE, "added": 1, "removed": 0}])]


def test_a_save_during_an_ai_turn_does_not_swallow_the_ais_edits(session, code, monkeypatch):
    other = "backend/workspace/app/other.py"
    code.files[other] = "a\n"
    interview._attribute(session, "manual")  # snapshot now includes other.py
    monkeypatch.setitem(interview._procs, "assistant", object())  # the AI is mid-turn
    code.files[other] = "a\nai\nai\n"  # the AI edits other.py
    before = code.files[FILE]
    code.files[FILE] = before + "# me\n"  # ...while you save service.py
    interview.record_manual_save(FILE, before, code.files[FILE])
    interview._procs.clear()
    interview._attribute(session, "ai")  # the turn ends
    assert changes(session["session_id"])[-2:] == [
        ("manual", [{"path": FILE, "added": 1, "removed": 0}]),
        ("ai", [{"path": other, "added": 2, "removed": 0}]),
    ]


def test_edits_made_outside_the_browser_count_as_yours_on_the_next_save(session, code):
    code.files[FILE] += "# from vscode\n"  # changed on disk, no editor save
    before = code.files[FILE]
    code.files[FILE] = before + "# then saved here\n"
    interview.record_manual_save(FILE, before, code.files[FILE])
    assert changes(session["session_id"]) == [("manual", [{"path": FILE, "added": 2, "removed": 0}])]


def test_saves_outside_the_interview_or_after_it_ended_are_ignored(client, session, code):
    interview.record_manual_save("backend/workspace/drills/ex01_dicts.py", "a\n", "b\n")
    assert changes(session["session_id"]) == []
    client.post("/api/interview/end")
    code.files[FILE] += "# late\n"
    interview.record_manual_save(FILE, "", code.files[FILE])
    assert changes(session["session_id"]) == []


def test_the_sessions_list_totals_lines_changed_by_you_and_by_the_ai(client, session, code):
    code.files[FILE] += "1\n2\n"
    interview._attribute(session, "manual")
    code.files[FILE] += "3\n"
    interview._attribute(session, "ai")
    summary = client.get("/api/interview/sessions").json()[0]
    assert (summary["manual_lines"], summary["ai_lines"]) == (2, 1)


# ── grades ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("verdict_line", "expected"),
    [
        ("**Strong hire**: great.", "Strong hire"),
        ("Lean no hire. Didn't verify.", "Lean no hire"),
        ("No hire: ran out of time.", "No hire"),
        ("Lean hire: solid.", "Lean hire"),
        ("Hire, clear communication.", "Hire"),
        ("Undecided", None),
    ],
)
def test_parse_grade_reads_the_verdict(verdict_line, expected):
    assert interview._parse_grade(f"## Verdict\n{verdict_line}\n\n## Scores\n")["verdict"] == expected


def test_parse_grade_reads_scores_in_any_reasonable_format():
    text = """## Scores (1-4)
| Dimension | Score | Evidence |
|---|---|---|
| Debugging & problem solving | 3 | found it |
| **Communication** | **2** | quiet |
| Verification | 4/4 | ran tests |
| Notes | n/a | - |
"""
    assert interview._parse_grade(text)["scores"] == {"Debugging & problem solving": 3, "Communication": 2, "Verification": 4}


# ── attention, time, the grader's log ─────────────────────────────────────────


def test_activity_text_is_empty_without_tracking_and_lists_targets_with_it():
    empty = {"active": 0, "idle": 0, "away": 0, "keys": 0, "clicks": 0, "scrolls": 0, "targets": [], "files_opened": [], "idle_gaps": []}
    assert interview._activity_text(empty) == "No activity data (tracker not running)."
    full = {
        **empty,
        "active": 90,
        "targets": [{"target": "panel:ticket", "seconds": 90, "keys": 0, "clicks": 1, "scrolls": 2}],
        "files_opened": [{"path": "README.md", "at": 5}],
        "idle_gaps": [{"at": 300, "seconds": 150, "away": True}],
    }
    text = interview._activity_text(full)
    assert "Active 1:30" in text and "panel:ticket: 1:30" in text and "README.md @0:05" in text and "2:30 at 5:00 (away)" in text


def test_elapsed_subtracts_finished_and_ongoing_pauses(clock):
    started = clock.now
    st = {"started_at": started.isoformat(), "paused_seconds": 60}
    clock.advance(300)
    assert interview._elapsed(st) == 240
    st["paused_at"] = (started + timedelta(seconds=200)).isoformat()  # paused 100s ago
    assert interview._elapsed(st) == 140


def test_format_log_skips_raw_activity_and_truncates_long_text():
    log = interview._format_log(
        [
            {"t": "x", "elapsed": 65, "kind": "note", "text": "hi"},
            {"t": "x", "elapsed": 70, "kind": "activity", "seconds": {}},
            {"t": "x", "elapsed": 80, "kind": "reply", "text": "r" * 5000},
            {"t": "x", "elapsed": 90, "kind": "code_change", "diff": "d" * 9000},
        ]
    )
    lines = log.splitlines()
    assert lines[0] == '[01:05] note: {"text": "hi"}'
    assert len(lines) == 3 and "activity" not in log
    assert lines[1].count("r") <= 1510 and lines[2].count("d") <= 2510


# ── config helpers ────────────────────────────────────────────────────────────


def test_app_dirs_for_stock_and_generated_apps():
    assert interview.app_dirs({"app": "payouts"}) == {
        "api": "backend/workspace/payouts",
        "backend_tests": "backend/tests/payouts",
        "frontend_tests": "frontend/tests/payouts",
    }
    assert interview.app_dirs({"app": "gen_x", "generated": True})["api"] == "backend/workspace/gen/gen_x"


def test_every_private_folder_is_denied_to_every_file_tool():
    rules = interview._deny_rules()
    for folder in interview.PRIVATE_DIRS:
        for tool in ("Read", "Edit", "Write", "Grep", "Glob"):
            assert any(r.startswith(f"{tool}(") and f"{folder}/**" in r for r in rules), (tool, folder)


def test_proc_keys_keep_the_sandbox_separate():
    assert interview._proc_key("assistant", {"sandbox": True}) == "sandbox:assistant"
    assert interview._proc_key("assistant", {}) == "assistant"
    assert interview._proc_key("grader", None) == "grader"


def test_scenarios_are_ordered_sandbox_first_then_by_attempt():
    ids = [c["id"] for c in interview.load_configs() if not c.get("generated")]
    assert ids[:5] == ["ai0", "ai1", "ai2", "ai3", "ai4"]

