"""Sanity-check the training content (maintainer tool; it never touches your working copies).

In a temporary directory it:
  1. runs every exercise against its pristine STARTER -> each must FAIL (exercises start broken)
  2. overlays the reference SOLUTIONS              -> each must PASS

Usage:  uv run python scripts/verify_solutions.py      (or: npm run verify)
"""

import dataclasses
import os
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from trainer import paths  # noqa: E402
from trainer.catalog import Exercise, TestSuite, load_catalog  # noqa: E402
from trainer.runner import run_exercise  # noqa: E402


def copy_tree(src: Path, dst: Path) -> None:
    for file in src.rglob("*"):
        if file.is_file() and "__pycache__" not in file.parts:
            target = dst / file.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)


INTERVIEW_DIR = paths.BACKEND_DIR / "interview"


def interview_feature_exercises() -> list[Exercise]:
    """Each AI-interview feature request as its own exercise (its suites aren't in the catalog)."""
    catalog = load_catalog()
    extra = []
    for config_path in sorted(INTERVIEW_DIR.glob("*.toml")):
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        base = catalog[config["id"]]
        for feature in config.get("feature", []):
            extra.append(
                dataclasses.replace(
                    base,
                    id=f"{base.id}:{feature['id']}",
                    title=f"{base.title} / feature: {feature['title']}",
                    tests=[TestSuite(**t) for t in feature["tests"]],
                )
            )
    return extra


def run_all(label: str, expect_ok: bool) -> list[str]:
    problems = []
    print(f"\n== {label} (expect {'PASS' if expect_ok else 'FAIL'}) ==")
    for ex in [*load_catalog().values(), *interview_feature_exercises()]:
        result = run_exercise(ex)
        verdict = "PASS" if result["ok"] else "FAIL"
        good = result["ok"] == expect_ok
        mark = "ok " if good else "XX "
        print(f"  {mark}{ex.id:11} {verdict}  {result['passed']}/{result['total']}  {ex.title}")
        if not good:
            problems.append(f"{label}: {ex.id}")
            if expect_ok:
                for case in result["cases"]:
                    if case["status"] in ("failed", "error"):
                        print(f"        - {case['name']}: {case['message']}")
    return problems


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="verify-") as tmp_name:
        tmp = Path(tmp_name)
        workspace = tmp / "workspace"
        frontend_clinic = tmp / "frontend_clinic"
        copy_tree(paths.STARTERS_DIR / "drills", workspace / "drills")
        copy_tree(paths.STARTERS_DIR / "clinic", workspace / "clinic")
        copy_tree(paths.STARTERS_DIR / "booking", workspace / "booking")
        copy_tree(paths.STARTERS_DIR / "frontend", frontend_clinic)
        os.environ["TRAINER_WORKSPACE"] = str(workspace)
        os.environ["CLINIC_SRC_DIR"] = str(frontend_clinic)
        for app in paths.INTERVIEW_APPS:  # vite.config.ts reads <APP>_SRC_DIR
            copy_tree(paths.STARTERS_DIR / app, workspace / app)
            copy_tree(paths.STARTERS_DIR / f"{app}_web", tmp / f"frontend_{app}")
            os.environ[f"{app.upper()}_SRC_DIR"] = str(tmp / f"frontend_{app}")

        problems = run_all("starters", expect_ok=False)

        copy_tree(paths.SOLUTIONS_DIR / "drills", workspace / "drills")
        copy_tree(paths.SOLUTIONS_DIR / "clinic", workspace / "clinic")
        copy_tree(paths.SOLUTIONS_DIR / "booking", workspace / "booking")
        copy_tree(paths.SOLUTIONS_DIR / "frontend", frontend_clinic)
        for app in paths.INTERVIEW_APPS:
            copy_tree(paths.SOLUTIONS_DIR / app, workspace / app)
            copy_tree(paths.SOLUTIONS_DIR / f"{app}_web", tmp / f"frontend_{app}")
        problems += run_all("solutions", expect_ok=True)

    print()
    if problems:
        print("Problems: " + ", ".join(problems))
        return 1
    print("All exercises start broken and all reference solutions pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
