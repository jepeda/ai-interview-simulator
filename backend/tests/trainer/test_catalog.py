"""Self-checks for the training infrastructure (these should always pass)."""

from trainer.catalog import load_catalog
from trainer.paths import QUICKREF_DIR, REPO_ROOT, SOLUTIONS_DIR, STARTERS_DIR
from trainer.workspace import starter_for


def test_catalog_tracks():
    tracks = [ex.track for ex in load_catalog().values()]
    assert tracks.count("syntax") == 15
    assert tracks.count("debugging") == 5
    assert tracks.count("project") >= 1


def test_every_exercise_file_has_a_starter_and_solutions_are_separate():
    for ex in load_catalog().values():
        solutions = []
        for work_file in ex.files:
            starter = starter_for(work_file)
            assert starter.is_file(), f"{ex.id}: missing starter {starter}"
            solution = SOLUTIONS_DIR / starter.relative_to(STARTERS_DIR)
            if solution.is_file():
                assert solution.read_bytes() != starter.read_bytes(), f"{ex.id}: {work_file} starts solved"
                solutions.append(solution)
        assert solutions, f"{ex.id}: no reference solution"


def test_every_test_suite_exists():
    for ex in load_catalog().values():
        assert ex.tests, ex.id
        for suite in ex.tests:
            assert suite.runner in {"pytest", "vitest"}
            assert (REPO_ROOT / suite.path).is_file(), f"{ex.id}: missing {suite.path}"


def test_every_exercise_has_requirements_and_hints():
    for ex in load_catalog().values():
        assert ex.requirements.strip(), ex.id
        assert len(ex.hints) >= 2, ex.id


def test_every_quickref_page_exists_and_has_a_title():
    for ex in load_catalog().values():
        assert ex.quickref, f"{ex.id}: no quickref pages"
        for page in ex.quickref:
            path = QUICKREF_DIR / f"{page}.md"
            assert path.is_file(), f"{ex.id}: missing {path}"
            assert path.read_text(encoding="utf-8").startswith("# "), f"{path} must start with '# Title'"
