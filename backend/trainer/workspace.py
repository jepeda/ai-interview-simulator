"""Create, reset and inspect the working copies of exercise files.

Starters (backend/starters) are the pristine, broken versions and are never edited.
Your edits happen in the working copies (backend/workspace, frontend/src/clinic/patientState.ts).
"""

import shutil
from pathlib import Path

from trainer.paths import MAPPINGS, REPO_ROOT


def starter_files(starter_dir: Path) -> list[Path]:
    return sorted(
        p for p in starter_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )


def starter_for(work_rel_path: str) -> Path:
    """Map a repo-relative working-copy path to its starter file."""
    work_path = (REPO_ROOT / work_rel_path).resolve()  # works for files and folders
    for starter_dir, work_dir in MAPPINGS:
        if work_path.is_relative_to(work_dir.resolve()):
            return starter_dir / work_path.relative_to(work_dir.resolve())
    raise ValueError(f"{work_rel_path} is not an exercise working file")


def init_workspace() -> list[Path]:
    """Copy every starter file whose working copy does not exist yet. Never overwrites."""
    created: list[Path] = []
    for starter_dir, work_dir in MAPPINGS:
        for starter in starter_files(starter_dir):
            target = work_dir / starter.relative_to(starter_dir)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(starter, target)
                created.append(target)
    return created


def reset_files(work_rel_paths: list[str]) -> list[Path]:
    """Overwrite the given working copies with their starters."""
    restored: list[Path] = []
    for work_rel in work_rel_paths:
        starter = starter_for(work_rel)
        target = REPO_ROOT / work_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(starter, target)
        restored.append(target)
    return restored


def is_modified(work_rel_path: str) -> bool:
    target = REPO_ROOT / work_rel_path
    if not target.exists():
        return True
    return target.read_bytes() != starter_for(work_rel_path).read_bytes()
