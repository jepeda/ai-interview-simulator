import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
STARTERS_DIR = BACKEND_DIR / "starters"
SOLUTIONS_DIR = BACKEND_DIR / "solutions"
WORKSPACE_DIR = BACKEND_DIR / "workspace"
DATA_DIR = BACKEND_DIR / "data"
CATALOG_PATH = BACKEND_DIR / "catalog.toml"
CHEATSHEET_PATH = REPO_ROOT / "docs" / "ts-to-python.md"
QUICKREF_DIR = REPO_ROOT / "docs" / "quickref"

# AI-interview apps: backend/starters/<app> -> backend/workspace/<app> and
# backend/starters/<app>_web -> frontend/src/<app> (ports 8713, 8714, 8715; the sandbox demo on 8716).
INTERVIEW_APPS = ["payouts", "remits", "earnings", "sandbox", "warmup"]  # warmup: 8717

# Generated interview scenarios (trainer/generate.py): one package per scenario, e.g.
# backend/starters/gen/gen_eligibility -> backend/workspace/gen/gen_eligibility and
# backend/starters/gen_web/gen_eligibility -> frontend/src/gen/gen_eligibility. Gitignored.
GEN_STARTERS_DIR = STARTERS_DIR / "gen"
GEN_WEB_STARTERS_DIR = STARTERS_DIR / "gen_web"
GEN_WORKSPACE_DIR = WORKSPACE_DIR / "gen"
GEN_WEB_WORKSPACE_DIR = FRONTEND_DIR / "src" / "gen"
GENERATED_CONFIG_DIR = BACKEND_DIR / "interview" / "generated"

# (starter directory, working-copy directory). Each file under a starter directory is
# copied to the same relative path under its working directory.
MAPPINGS: list[tuple[Path, Path]] = [
    (STARTERS_DIR / "drills", WORKSPACE_DIR / "drills"),
    (STARTERS_DIR / "clinic", WORKSPACE_DIR / "clinic"),
    (STARTERS_DIR / "booking", WORKSPACE_DIR / "booking"),
    (STARTERS_DIR / "frontend", FRONTEND_DIR / "src" / "clinic"),
    *[
        pair
        for app in INTERVIEW_APPS
        for pair in (
            (STARTERS_DIR / app, WORKSPACE_DIR / app),
            (STARTERS_DIR / f"{app}_web", FRONTEND_DIR / "src" / app),
        )
    ],
    (GEN_STARTERS_DIR, GEN_WORKSPACE_DIR),
    (GEN_WEB_STARTERS_DIR, GEN_WEB_WORKSPACE_DIR),
]


def generated_config_files() -> list[Path]:
    """Configs of generated scenarios. Drafts (`*.draft.toml`, not verified yet) are skipped unless
    TRAINER_INCLUDE_DRAFTS=1 (the verifier sets it)."""
    files = sorted(GENERATED_CONFIG_DIR.glob("*.toml"))
    if os.environ.get("TRAINER_INCLUDE_DRAFTS") != "1":
        files = [f for f in files if not f.name.endswith(".draft.toml")]
    return files


def rel(path: Path) -> str:
    """Repo-relative path with forward slashes (stable across Windows and macOS)."""
    return path.resolve().relative_to(REPO_ROOT).as_posix()
