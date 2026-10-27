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
]


def rel(path: Path) -> str:
    """Repo-relative path with forward slashes (stable across Windows and macOS)."""
    return path.resolve().relative_to(REPO_ROOT).as_posix()
