"""Every mock-interview scenario is complete and wired up: config keys, catalog entry, tests, apps,
ports and pages. (Whether its starters fail and its solutions pass is `npm run verify`.)"""

import json
import re

import pytest

from trainer import interview
from trainer.catalog import load_catalog
from trainer.paths import FRONTEND_DIR, INTERVIEW_APPS, REPO_ROOT, SOLUTIONS_DIR, STARTERS_DIR

CONFIGS = [c for c in interview.load_configs() if not c.get("generated")]
REQUIRED = ["id", "title", "minutes", "order", "app", "api_port", "portal_path", "portal_title", "app_summary", "company_context", "ticket", "interviewer_notes"]


def test_there_are_the_stock_scenarios():
    assert [c["id"] for c in CONFIGS] == ["ai0", "ai1", "ai2", "ai3", "ai4"]
    assert [c["id"] for c in CONFIGS if c.get("sandbox")] == ["ai0"]


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_config_has_every_key(cfg):
    missing = [k for k in REQUIRED if k not in cfg or cfg[k] in ("", None)]
    assert not missing, f"{cfg['id']} is missing {missing}"
    assert cfg["minutes"] in (15, 30, 60)


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_config_is_an_interview_exercise_in_the_catalog(cfg):
    ex = load_catalog()[cfg["id"]]
    assert ex.track == "interview" and ex.minutes == cfg["minutes"]
    assert ex.root == f"backend/workspace/{cfg['app']}" and ex.extra_roots == [f"frontend/src/{cfg['app']}"]


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_ticket_names_the_bug_tests_that_exist(cfg):
    ex = load_catalog()[cfg["id"]]
    assert {t.runner for t in ex.tests} == {"pytest", "vitest"}  # full stack: a backend and a frontend part
    for suite in ex.tests:
        assert (REPO_ROOT / suite.path).is_file(), suite.path
        assert suite.path in cfg["ticket"], f"{cfg['id']}: the ticket should point at {suite.path}"


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_features_are_complete_and_have_their_own_tests(cfg):
    features = cfg.get("feature", [])
    assert 1 <= len(features) <= 3
    bug_tests = {t.path for t in load_catalog()[cfg["id"]].tests}
    for f in features:
        assert all(f.get(k) for k in ("id", "title", "summary", "spec", "interviewer_notes", "tests")), f["id"]
        for t in f["tests"]:
            assert (REPO_ROOT / t["path"]).is_file() and t["path"] not in bug_tests


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_app_has_starters_solutions_and_a_page(cfg):
    app = cfg["app"]
    assert app in INTERVIEW_APPS
    assert (STARTERS_DIR / app / "main.py").is_file() and (STARTERS_DIR / app / "README.md").is_file()
    assert (STARTERS_DIR / f"{app}_web" / "main.tsx").is_file()
    assert any((SOLUTIONS_DIR / app).rglob("*.py")), f"{app}: no backend solution"
    assert (FRONTEND_DIR / cfg["portal_path"].lstrip("/")).is_file(), cfg["portal_path"]


def test_every_app_has_its_own_port_proxy_and_dev_script():
    ports = [c["api_port"] for c in CONFIGS]
    assert len(set(ports)) == len(ports)
    vite = (FRONTEND_DIR / "vite.config.ts").read_text()
    scripts = json.loads((REPO_ROOT / "package.json").read_text())["scripts"]
    for c in CONFIGS:
        assert re.search(rf'name: "{c["app"]}", port: {c["api_port"]}', vite), c["app"]
        assert f"--port {c['api_port']}" in scripts[f"dev:{c['app']}"]
        assert f'"npm:dev:{c["app"]}"' in scripts["dev"], f"npm run dev doesn't start {c['app']}"


def test_working_copies_and_generated_content_are_gitignored():
    ignored = (REPO_ROOT / ".gitignore").read_text()
    for entry in ["backend/workspace/", "backend/data/", "backend/starters/gen/", "backend/solutions/gen/", "backend/interview/generated/", "frontend/src/gen/"]:
        assert entry in ignored, entry
    for app in INTERVIEW_APPS:
        assert f"frontend/src/{app}/" in ignored, app


def test_no_real_company_name_in_the_shipped_scenarios():
    for path in [*(REPO_ROOT / "backend" / "interview").glob("*.toml"), REPO_ROOT / "README.md"]:
        assert "headway" not in path.read_text().lower(), path.name
