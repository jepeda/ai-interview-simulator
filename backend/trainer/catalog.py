import tomllib
from dataclasses import dataclass, field
from functools import cache

from trainer.paths import CATALOG_PATH, REPO_ROOT, generated_config_files, rel
from trainer.workspace import starter_files, starter_for


@dataclass(frozen=True)
class TestSuite:
    runner: str  # "pytest" | "vitest"
    path: str  # repo-relative


@dataclass(frozen=True)
class Exercise:
    id: str
    track: str
    title: str
    minutes: int
    topics: list[str]
    files: list[str]
    tests: list[TestSuite]
    requirements: str
    hints: list[str]
    root: str | None = None  # folder shown in the editor's file tree (repo-relative)
    extra_roots: list[str] = field(default_factory=list)  # more editable folders (e.g. a frontend)
    quickref: list[str] = field(default_factory=list)  # docs/quickref pages relevant to this exercise


def roots_of(ex: Exercise) -> list[str]:
    """Every folder whose files (including ones you create) belong to the exercise."""
    return [ex.root, *ex.extra_roots] if ex.root else []


@cache
def load_catalog() -> dict[str, Exercise]:
    with CATALOG_PATH.open("rb") as f:
        raw = tomllib.load(f)
    items = list(raw["exercise"])
    for path in generated_config_files():  # generated scenarios carry their own [exercise] table
        try:
            with path.open("rb") as f:
                items.append(tomllib.load(f)["exercise"])
        except (tomllib.TOMLDecodeError, KeyError):
            continue  # a broken generated scenario must not take the trainer down
    exercises: dict[str, Exercise] = {}
    for item in items:
        root = item.get("root")
        files = item.get("files")
        if files is None:
            # Project exercises: every file of the package is part of the exercise (and of reset).
            if root is None:
                raise ValueError(f"{item['id']}: give `files` or `root`")
            files = []
            for folder in [root, *item.get("extra_roots", [])]:
                starter_dir = starter_for(folder)
                files += [rel(REPO_ROOT / folder / f.relative_to(starter_dir)) for f in starter_files(starter_dir)]
        ex = Exercise(
            id=item["id"],
            track=item["track"],
            title=item["title"],
            minutes=item["minutes"],
            topics=item.get("topics", []),
            files=files,
            tests=[TestSuite(**t) for t in item["tests"]],
            requirements=item["requirements"].strip(),
            hints=[h.strip() for h in item.get("hints", [])],
            root=root,
            extra_roots=item.get("extra_roots", []),
            quickref=item.get("quickref", []),
        )
        if ex.id in exercises:
            raise ValueError(f"Duplicate exercise id {ex.id}")
        exercises[ex.id] = ex
    return exercises
