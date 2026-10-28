"""The scenario generator: naming, ports, the agent's permissions and prompt, draft gating, the
content check's failure modes, and the job/scenario endpoints. Claude is never called."""

import io
import json
from pathlib import Path

import pytest

from trainer import generate, interview, paths
from trainer.catalog import load_catalog

GENERATED_TOML = """
id = "gen_acme"
title = "Acme: wrong totals"
minutes = 30
order = 10
generated = true
app = "gen_acme"
api_port = 8725
portal_path = "/src/gen/gen_acme/index.html"
ticket = "t"

[exercise]
id = "gen_acme"
track = "interview"
title = "Acme (30 min)"
minutes = 30
root = "backend/workspace/gen/gen_acme"
extra_roots = ["frontend/src/gen/gen_acme"]
tests = [{ runner = "pytest", path = "backend/tests/gen/gen_acme/test_gen_acme_bug.py" }]
requirements = "r"
hints = ["a", "b"]
"""


@pytest.fixture
def gen_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty backend/interview/generated + gen starters folder."""
    folder = tmp_path / "generated"
    folder.mkdir()
    monkeypatch.setattr(paths, "GENERATED_CONFIG_DIR", folder)
    monkeypatch.setattr(generate, "GENERATED_CONFIG_DIR", folder)
    monkeypatch.setattr(generate, "GEN_STARTERS_DIR", tmp_path / "starters_gen")
    monkeypatch.delenv("TRAINER_INCLUDE_DRAFTS", raising=False)
    load_catalog.cache_clear()
    yield folder
    load_catalog.cache_clear()


# ── drafts ────────────────────────────────────────────────────────────────────


def test_drafts_are_hidden_until_verified(gen_dir, monkeypatch):
    (gen_dir / "gen_acme.draft.toml").write_text(GENERATED_TOML)
    assert paths.generated_config_files() == []
    assert "gen_acme" not in load_catalog()
    assert all(c["id"] != "gen_acme" for c in interview.load_configs())
    monkeypatch.setenv("TRAINER_INCLUDE_DRAFTS", "1")  # what the content check sets
    assert [p.name for p in paths.generated_config_files()] == ["gen_acme.draft.toml"]


def test_a_published_scenario_joins_the_catalog_and_the_scenario_list(gen_dir):
    (gen_dir / "gen_acme.toml").write_text(GENERATED_TOML)
    ex = load_catalog()["gen_acme"]
    assert ex.track == "interview" and ex.root == "backend/workspace/gen/gen_acme"
    cfg = interview.load_config("gen_acme")
    assert cfg["generated"] is True and interview.app_dirs(cfg)["api"] == "backend/workspace/gen/gen_acme"


def test_a_broken_generated_file_is_skipped_instead_of_crashing(gen_dir):
    (gen_dir / "gen_bad.toml").write_text("id = [unclosed")
    (gen_dir / "gen_noexercise.toml").write_text('id = "gen_noexercise"\ntitle = "x"\n')
    assert "ai1" in load_catalog()  # still loads
    assert [c["id"] for c in interview.load_configs() if c["id"].startswith("gen")] == ["gen_noexercise"]


# ── names, ports ──────────────────────────────────────────────────────────────


def test_package_names_are_python_identifiers_and_unique(gen_dir, data_dir):
    assert generate._package_name("Spotify, Inc.", "") == "gen_spotify_inc"
    assert generate._package_name("", "Insurance eligibility checks!") == "gen_insurance_eligibility_ch"
    assert generate._package_name("", "") == "gen_scenario"
    (generate.GEN_STARTERS_DIR / "gen_spotify").mkdir(parents=True)
    assert generate._package_name("Spotify", "") == "gen_spotify_2"
    assert generate._package_name("Payouts", "") == "gen_payouts"  # stock apps don't use the gen_ prefix


def test_ports_skip_ones_already_taken(gen_dir, data_dir):
    assert generate._free_port() == generate.FIRST_PORT
    (gen_dir / "gen_acme.toml").write_text(GENERATED_TOML.replace("8725", str(generate.FIRST_PORT)))
    generate._save_job({"id": "j1", "pkg": "gen_x", "port": generate.FIRST_PORT + 1, "status": "failed"})
    assert generate._free_port() == generate.FIRST_PORT + 2


# ── the agent ─────────────────────────────────────────────────────────────────


def test_the_agent_may_only_write_its_own_package():
    args = generate._claude_args({"pkg": "gen_acme"})
    allowed = args[args.index("--allowedTools") + 1 : args.index("--disallowedTools")]
    writes = [a for a in allowed if a.startswith(("Write(", "Edit("))]
    assert writes and all("gen_acme" in a for a in writes)
    assert not any("backend/trainer" in a or "catalog.toml" in a for a in writes)
    assert "Bash(uv run python scripts/verify_solutions.py --only gen_acme)" in allowed
    assert not any(a == "Bash" or a.startswith("Bash(rm") for a in allowed)
    denied = args[args.index("--disallowedTools") + 1 :]
    assert any("backend/data" in d and d.startswith("Read(") for d in denied)  # your logs stay private
    assert args[args.index("--permission-mode") + 1] == "dontAsk"


def test_the_prompt_uses_the_company_and_the_scenario_settings():
    job = {"pkg": "gen_acme", "port": 8725, "minutes": 30, "difficulty": "hard", "company": "Acme Corp", "domain": "they sell anvils", "order": 11}
    prompt = generate._prompt(job)
    assert "**Acme Corp**" in prompt and "they sell anvils" in prompt
    assert "gen_acme" in prompt and "8725" in prompt and "order = 11" in prompt
    assert "2 feature requests" in prompt and generate.DIFFICULTY["hard"] in prompt
    assert "Never describe the bug" in prompt


def test_without_a_company_the_prompt_asks_for_a_fictional_one():
    base = {"pkg": "gen_x", "port": 8720, "minutes": 60, "difficulty": "standard", "order": 10}
    assert "fictional company" in generate._prompt({**base, "company": "", "domain": "dental billing"})
    assert "3 feature requests" in generate._prompt({**base, "company": "", "domain": ""})


# ── the content check ─────────────────────────────────────────────────────────


def test_verify_fails_without_a_config(gen_dir):
    assert "didn't write" in generate._verify({"pkg": "gen_acme"}, io.StringIO())


def test_verify_fails_on_invalid_toml(gen_dir):
    (gen_dir / "gen_acme.draft.toml").write_text("id = ")
    assert "isn't valid TOML" in generate._verify({"pkg": "gen_acme"}, io.StringIO())


@pytest.mark.parametrize(
    ("returncode", "stdout", "expected"),
    [
        (1, "  XX gen_acme    PASS  4/4  x\n", "content check failed"),
        (0, "All exercises start broken and all reference solutions pass.\n", "didn't find the scenario's tests"),
        (0, "  ok gen_acme    FAIL\n  ok gen_acme:f FAIL\n  ok gen_acme    PASS\n  ok gen_acme:f PASS\n", None),
    ],
)
def test_verify_reads_the_content_check(gen_dir, monkeypatch, returncode, stdout, expected):
    (gen_dir / "gen_acme.draft.toml").write_text(GENERATED_TOML)

    class Done:
        def __init__(self):
            self.returncode, self.stdout, self.stderr = returncode, stdout, ""

    monkeypatch.setattr(generate.subprocess, "run", lambda *a, **k: Done())
    error = generate._verify({"pkg": "gen_acme"}, io.StringIO())
    assert (error is None) if expected is None else (expected in error)


# ── endpoints ─────────────────────────────────────────────────────────────────


def test_a_job_that_was_running_when_the_trainer_restarted_is_marked_interrupted(client, gen_dir, monkeypatch):
    removed = []
    monkeypatch.setattr(generate, "_remove_scenario", removed.append)
    generate._save_job({"id": "j1", "pkg": "gen_acme", "port": 8720, "status": "running"})
    job = client.get("/api/generate").json()[0]
    assert job["status"] == "failed" and "Interrupted" in job["error"] and removed == ["gen_acme"]


def test_only_one_generation_at_a_time(client, gen_dir, monkeypatch):
    monkeypatch.setitem(generate._threads, "j1", object())
    generate._save_job({"id": "j1", "pkg": "gen_acme", "port": 8720, "status": "running"})
    assert client.post("/api/generate", json={"company": "X"}).status_code == 409
    assert client.post("/api/generate/j1/dismiss").status_code == 409  # can't dismiss a running job


def test_starting_a_job_records_it_and_runs_it_in_the_background(client, gen_dir, monkeypatch):
    started = []
    monkeypatch.setattr(generate, "_threads", {})
    monkeypatch.setattr(generate, "_run", started.append)
    monkeypatch.setattr(interview, "_claude_command", lambda: ["claude"])
    job = client.post("/api/generate", json={"company": "Acme", "minutes": 30, "difficulty": "warmup"}).json()
    assert job["status"] == "running" and job["pkg"] == "gen_acme" and job["minutes"] == 30
    generate._threads[job["id"]].join(timeout=5)
    assert started and started[0]["id"] == job["id"]
    assert json.loads(generate.JOBS_PATH.read_text())[0]["id"] == job["id"]


def test_invalid_generation_settings_are_rejected(client, gen_dir):
    assert client.post("/api/generate", json={"minutes": 45}).status_code == 422
    assert client.post("/api/generate", json={"difficulty": "insane"}).status_code == 422


def test_dismissing_a_finished_job_removes_it(client, gen_dir):
    generate._save_job({"id": "j1", "pkg": "gen_acme", "port": 8720, "status": "failed"})
    client.post("/api/generate/j1/dismiss")
    assert client.get("/api/generate").json() == []


def test_deleting_a_generated_scenario(client, gen_dir, monkeypatch):
    removed = []
    monkeypatch.setattr(generate, "_remove_scenario", removed.append)
    assert client.delete("/api/generate/scenario/ai1").status_code == 404  # stock scenarios can't be deleted
    (gen_dir / "gen_acme.toml").write_text(GENERATED_TOML)
    interview._write_state({"session_id": "s1", "exercise": "gen_acme", "started_at": "2026-10-26T15:00:00+00:00", "ended_at": None})
    assert client.delete("/api/generate/scenario/gen_acme").status_code == 409  # mid-interview
    interview._write_state({"session_id": "s1", "exercise": "gen_acme", "started_at": "2026-10-26T15:00:00+00:00", "ended_at": "x"})
    assert client.delete("/api/generate/scenario/gen_acme").json() == {"ok": True}
    assert removed == ["gen_acme"]


def test_scenario_paths_cover_every_folder_of_a_package():
    found = {p.relative_to(paths.REPO_ROOT).as_posix() for p in generate.scenario_paths("gen_acme")}
    for expected in (
        "backend/starters/gen/gen_acme",
        "backend/starters/gen_web/gen_acme",
        "backend/solutions/gen/gen_acme",
        "backend/solutions/gen_web/gen_acme",
        "backend/tests/gen/gen_acme",
        "frontend/tests/gen/gen_acme",
        "backend/workspace/gen/gen_acme",
        "frontend/src/gen/gen_acme",
    ):
        assert expected in found
