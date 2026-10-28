"""The mock-interview engine through its HTTP API: sessions, stages, features, pause, the sandbox's
separate slot, notes, chat and grading. All side effects are faked (see conftest.py)."""

import json

import pytest
from trainer_testkit import events, kinds, state

from trainer import interview

REAL = "ai4"  # the 30-minute warmup
SANDBOX = "ai0"
SANDBOX_H = {"X-Interview-Scenario": SANDBOX}
REAL_H = {"X-Interview-Scenario": REAL}


def start(client, scenario: str = REAL) -> dict:
    headers = SANDBOX_H if scenario == SANDBOX else REAL_H
    res = client.post("/api/interview/start", json={"scenario": scenario, "reset_code": True}, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def bug_suites(scenario: str = REAL) -> list[str]:
    return [t.path for t in interview._exercise(interview.load_config(scenario)).tests]


# ── sessions ──────────────────────────────────────────────────────────────────


def test_start_creates_a_session_with_meta_and_a_start_event(client):
    snap = start(client)
    session = snap["session"]
    assert session["exercise"] == REAL and session["stage"] == "bug" and session["ended_at"] is None
    assert snap["config"]["id"] == REAL and snap["config"]["minutes"] == 30
    meta = json.loads((interview.SESSIONS_DIR / session["session_id"] / "meta.json").read_text())
    assert meta == {"scenario": REAL, "title": snap["config"]["title"], "order": 4, "sandbox": False}
    assert kinds(session["session_id"]) == ["start"]


def test_get_returns_the_running_session_only_for_its_scenario(client):
    sid = start(client)["session"]["session_id"]
    assert client.get(f"/api/interview?scenario={REAL}").json()["session"]["session_id"] == sid
    other = client.get("/api/interview?scenario=ai1").json()
    assert other["session"] is None
    assert other["active"]["scenario"] == REAL  # the start screen warns that ai4 is still running


def test_starting_another_real_interview_ends_the_running_one(client, clock):
    first = start(client)["session"]["session_id"]
    clock.advance(60)
    second = start(client, "ai1")["session"]["session_id"]
    assert first != second
    end = [e for e in events(first) if e["kind"] == "end"]
    assert end and end[0]["reason"] == "replaced by a new interview"
    assert state()["session_id"] == second


def test_end_freezes_the_session_and_blocks_more_activity(client, clock):
    sid = start(client)["session"]["session_id"]
    clock.advance(125)
    snap = client.post("/api/interview/end", headers=REAL_H).json()
    assert snap["session"]["ended_at"] and snap["session"]["elapsed"] == 125
    assert (interview.SESSIONS_DIR / sid / "final.diff").exists()
    assert client.post("/api/interview/note", json={"text": "late"}, headers=REAL_H).status_code == 409
    assert client.post("/api/interview/chat", json={"persona": "interviewer", "message": "hi"}, headers=REAL_H).status_code == 409


def test_actions_without_an_interview_are_rejected(client):
    assert client.post("/api/interview/run", headers=REAL_H).status_code == 409
    assert client.post("/api/interview/note", json={"text": "x"}, headers=REAL_H).status_code == 409


def test_unknown_scenario_is_404(client):
    assert client.post("/api/interview/start", json={"scenario": "nope"}).status_code == 404


# ── tests, stages and features ────────────────────────────────────────────────


def test_failing_bug_tests_keep_the_features_locked(client, runner):
    sid = start(client)["session"]["session_id"]
    runner.failing = {bug_suites()[0]}
    snap = client.post("/api/interview/run", headers=REAL_H).json()
    assert snap["session"]["stage"] == "bug"
    assert all(f["spec"] is None for f in snap["config"]["features"])  # specs stay hidden
    run = [e for e in events(sid) if e["kind"] == "test_run"][-1]
    assert run["bug"] == [2, 4] and run["feature"] is None and run["failing"]


def test_passing_bug_tests_unlock_the_features(client):
    sid = start(client)["session"]["session_id"]
    snap = client.post("/api/interview/run", headers=REAL_H).json()
    assert snap["session"]["stage"] == "features"
    assert all(f["spec"] for f in snap["config"]["features"])
    assert "bug_fixed" in kinds(sid)


def test_features_can_only_be_chosen_after_the_bug(client):
    start(client)
    assert client.post("/api/interview/feature", json={"feature_id": "aging"}, headers=REAL_H).status_code == 409


def test_choosing_a_feature_adds_its_tests_and_finishing_it_is_logged(client, runner):
    sid = start(client)["session"]["session_id"]
    client.post("/api/interview/run", headers=REAL_H)
    assert client.post("/api/interview/feature", json={"feature_id": "nope"}, headers=REAL_H).status_code == 404
    client.post("/api/interview/feature", json={"feature_id": "aging"}, headers=REAL_H)
    feature_suite = "backend/tests/warmup/test_feature_aging.py"

    runner.failing = {feature_suite}
    client.post("/api/interview/run", headers=REAL_H)
    assert runner.calls[-1] == [*bug_suites(), feature_suite]
    assert "feature_done" not in kinds(sid)

    runner.failing = set()
    snap = client.post("/api/interview/run", headers=REAL_H).json()
    assert snap["session"]["feature_done"] is True
    assert [e["feature"] for e in events(sid) if e["kind"] == "feature_done"] == ["aging"]


# ── pause ─────────────────────────────────────────────────────────────────────


def test_pause_stops_the_clock_and_resume_restarts_it(client, clock):
    sid = start(client)["session"]["session_id"]
    clock.advance(100)
    client.post("/api/interview/pause", headers=REAL_H)
    clock.advance(600)  # ten minutes away
    assert client.get(f"/api/interview?scenario={REAL}").json()["session"]["elapsed"] == 100
    snap = client.post("/api/interview/resume", headers=REAL_H).json()
    assert snap["session"]["paused_seconds"] == 600 and snap["session"]["paused_at"] is None
    clock.advance(30)
    assert client.get(f"/api/interview?scenario={REAL}").json()["session"]["elapsed"] == 130
    resume = [e for e in events(sid) if e["kind"] == "resume"][0]
    assert resume["paused_for"] == 600


def test_nothing_happens_while_paused(client):
    start(client)
    client.post("/api/interview/pause", headers=REAL_H)
    assert client.post("/api/interview/run", headers=REAL_H).status_code == 409
    assert client.post("/api/interview/note", json={"text": "x"}, headers=REAL_H).status_code == 409
    assert client.post("/api/interview/chat", json={"persona": "assistant", "message": "x"}, headers=REAL_H).status_code == 409
    assert client.post("/api/interview/reset-data", headers=REAL_H).status_code == 409


def test_pausing_twice_and_resuming_when_not_paused_are_harmless(client, clock):
    sid = start(client)["session"]["session_id"]
    client.post("/api/interview/pause", headers=REAL_H)
    client.post("/api/interview/pause", headers=REAL_H)
    client.post("/api/interview/resume", headers=REAL_H)
    client.post("/api/interview/resume", headers=REAL_H)
    assert kinds(sid).count("pause") == 1 and kinds(sid).count("resume") == 1


def test_ending_while_paused_does_not_count_the_pause(client, clock):
    start(client)
    clock.advance(50)
    client.post("/api/interview/pause", headers=REAL_H)
    clock.advance(1000)
    assert client.post("/api/interview/end", headers=REAL_H).json()["session"]["elapsed"] == 50


# ── the sandbox slot ──────────────────────────────────────────────────────────


def test_the_sandbox_never_touches_a_real_interview(client, clock):
    real = start(client)["session"]["session_id"]
    clock.advance(5)
    sandbox = start(client, SANDBOX)["session"]["session_id"]
    assert state()["session_id"] == real and state()["ended_at"] is None  # still running
    assert state(sandbox=True)["session_id"] == sandbox and state(sandbox=True)["sandbox"] is True

    client.post("/api/interview/note", json={"text": "real"}, headers=REAL_H)
    client.post("/api/interview/note", json={"text": "demo"}, headers=SANDBOX_H)
    assert [e["text"] for e in events(real) if e["kind"] == "note"] == ["real"]
    assert [e["text"] for e in events(sandbox) if e["kind"] == "note"] == ["demo"]

    sandbox_view = client.get(f"/api/interview?scenario={SANDBOX}").json()
    assert sandbox_view["session"]["session_id"] == sandbox
    assert sandbox_view["active"] is None  # the sandbox doesn't warn about real interviews


def test_sandbox_sessions_are_flagged_in_the_sessions_list(client, clock):
    start(client)
    clock.advance(5)
    start(client, SANDBOX)
    flags = {s["scenario"]: s["sandbox"] for s in client.get("/api/interview/sessions").json()}
    assert flags == {REAL: False, SANDBOX: True}


# ── notes, activity ───────────────────────────────────────────────────────────


def test_notes_are_logged_with_their_source_and_empty_ones_rejected(client):
    sid = start(client)["session"]["session_id"]
    assert client.post("/api/interview/note", json={"text": "  "}, headers=REAL_H).status_code == 422
    client.post("/api/interview/note", json={"text": " hypothesis: UTC ", "source": "voice"}, headers=REAL_H)
    note = [e for e in events(sid) if e["kind"] == "note"][0]
    assert note["text"] == "hypothesis: UTC" and note["source"] == "voice"


def test_activity_batches_are_summarized_and_idle_gaps_logged(client):
    sid = start(client)["session"]["session_id"]
    batch = {
        "seconds": {"file:a.py": 30, "panel:ticket": 10},
        "idle": 5,
        "away": 0,
        "keys": {"file:a.py": 40},
        "clicks": {"panel:ticket": 3},
        "scrolls": {},
        "opened": [{"path": "a.py", "at": 2}],
        "idle_gaps": [{"at": 100, "seconds": 120, "away": True}],
    }
    client.post("/api/interview/activity", json=batch, headers=REAL_H)
    client.post("/api/interview/activity", json={**batch, "opened": [{"path": "a.py", "at": 50}, {"path": "b.py", "at": 60}], "idle_gaps": []}, headers=REAL_H)
    summary = client.get("/api/interview/activity", headers=REAL_H).json()
    assert summary["active"] == 80 and summary["idle"] == 10 and summary["keys"] == 80 and summary["clicks"] == 6
    assert summary["targets"][0] == {"target": "file:a.py", "seconds": 60, "keys": 80, "clicks": 0, "scrolls": 0}
    assert summary["files_opened"] == [{"path": "a.py", "at": 2}, {"path": "b.py", "at": 60}]  # first open only
    assert summary["idle_gaps"] == [{"at": 100, "seconds": 120, "away": True}]
    assert kinds(sid).count("idle") == 1


# ── chat and grading (Claude faked) ───────────────────────────────────────────


def fake_stream(reply: str, calls: list):
    def stream(persona, args, cwd, prompt, session_key, st):
        calls.append({"persona": persona, "args": args, "prompt": prompt})
        if st:
            interview._log(st, "reply", persona=persona, text=reply, tools=[], files_changed=[])
        yield interview._sse({"type": "done", "text": reply, "files_changed": []})

    return stream


def test_chat_logs_the_prompt_and_the_reply(client, monkeypatch):
    calls: list = []
    monkeypatch.setattr(interview, "_stream_claude", fake_stream("Hello!", calls))
    sid = start(client)["session"]["session_id"]
    res = client.post("/api/interview/chat", json={"persona": "interviewer", "message": "Which timezone?"}, headers=REAL_H)
    assert res.status_code == 200 and '"Hello!"' in res.text
    prompt, reply = [e for e in events(sid) if e["kind"] in ("prompt", "reply")]
    assert prompt["text"] == "Which timezone?" and prompt["persona"] == "interviewer" and reply["text"] == "Hello!"
    system = calls[0]["args"][calls[0]["args"].index("--append-system-prompt") + 1]
    assert "30-minute" in system and "Your private notes" in system  # the interviewer knows the answer


def test_a_second_message_while_claude_is_answering_is_rejected(client, monkeypatch):
    start(client)
    monkeypatch.setitem(interview._procs, "assistant", object())
    res = client.post("/api/interview/chat", json={"persona": "assistant", "message": "x"}, headers=REAL_H)
    assert res.status_code == 409


def test_the_assistant_is_scoped_to_the_app_and_denied_private_folders(client, monkeypatch):
    calls: list = []
    monkeypatch.setattr(interview, "_stream_claude", fake_stream("ok", calls))
    start(client)
    client.post("/api/interview/chat", json={"persona": "assistant", "message": "tour?", "active_file": "x.py"}, headers=REAL_H)
    args = calls[0]["args"]
    denied = args[args.index("--disallowedTools") + 1 : args.index("--add-dir")]
    assert any("backend/solutions" in d for d in denied) and any("backend/interview" in d for d in denied)
    assert "(IDE context: the candidate currently has x.py open.)" in calls[0]["prompt"]


def test_grading_saves_the_report_and_feeds_earlier_attempts_to_the_grader(client, clock, monkeypatch):
    calls: list = []
    report = "## Verdict\nLean hire: solid.\n\n## Scores (1-4)\n| Dimension | Score | Evidence |\n|---|---|---|\n| Debugging & problem solving | 3 | x |\n\n## What to do differently on Monday\n- Narrate more."
    monkeypatch.setattr(interview, "_stream_claude", fake_stream(report, calls))
    first = start(client)["session"]["session_id"]
    client.post("/api/interview/grade", headers=REAL_H)
    assert (interview.SESSIONS_DIR / first / "grade.md").read_text() == report
    assert "graded" in kinds(first)

    clock.advance(3600)
    start(client)
    client.post("/api/interview/grade", headers=REAL_H)
    previous = calls[-1]["prompt"].split("# Previous attempts")[1]
    assert first in previous and "verdict Lean hire" in previous and "Narrate more" in previous
    sessions = client.get("/api/interview/sessions").json()
    graded = next(s for s in sessions if s["session_id"] == first)
    assert graded["verdict"] == "Lean hire" and graded["scores"] == {"Debugging & problem solving": 3}


@pytest.mark.parametrize("persona", ["assistant", "interviewer"])
def test_cancel_kills_only_the_matching_slot(client, monkeypatch, persona):
    killed = []

    class Proc:
        def kill(self):
            killed.append(True)

    monkeypatch.setitem(interview._procs, f"sandbox:{persona}", Proc())
    assert client.post(f"/api/interview/chat/cancel?persona={persona}", headers=REAL_H).json() == {"cancelled": False}
    assert client.post(f"/api/interview/chat/cancel?persona={persona}", headers=SANDBOX_H).json() == {"cancelled": True}
    assert killed == [True]
