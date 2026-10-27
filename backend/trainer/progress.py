"""Progress tracking in SQLite (backend/data/progress.db). Plain sqlite3, no ORM."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from trainer.paths import DATA_DIR

DB_PATH = DATA_DIR / "progress.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS progress (
    exercise_id     TEXT PRIMARY KEY,
    status          TEXT NOT NULL DEFAULT 'not_started',  -- not_started | in_progress | completed
    hints_revealed  INTEGER NOT NULL DEFAULT 0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    times_completed INTEGER NOT NULL DEFAULT 0,
    completed_at    TEXT,
    last_result     TEXT
)
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _ensure_row(conn: sqlite3.Connection, exercise_id: str) -> None:
    conn.execute("INSERT OR IGNORE INTO progress (exercise_id) VALUES (?)", (exercise_id,))


def get_all() -> dict[str, dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM progress").fetchall()
    result = {}
    for row in rows:
        item = dict(row)
        item["last_result"] = json.loads(item["last_result"]) if item["last_result"] else None
        result[item["exercise_id"]] = item
    return result


def get(exercise_id: str) -> dict:
    return get_all().get(exercise_id) or {
        "exercise_id": exercise_id,
        "status": "not_started",
        "hints_revealed": 0,
        "attempts": 0,
        "times_completed": 0,
        "completed_at": None,
        "last_result": None,
    }


def record_run(exercise_id: str, result: dict) -> None:
    with _connect() as conn:
        _ensure_row(conn, exercise_id)
        conn.execute(
            "UPDATE progress SET attempts = attempts + 1, last_result = ? WHERE exercise_id = ?",
            (json.dumps(result), exercise_id),
        )
        if result["ok"]:
            conn.execute(
                """UPDATE progress
                   SET times_completed = times_completed + 1, completed_at = ?, status = 'completed'
                   WHERE exercise_id = ? AND status != 'completed'""",
                (_now(), exercise_id),
            )
        else:
            conn.execute(
                "UPDATE progress SET status = 'in_progress' WHERE exercise_id = ? AND status = 'not_started'",
                (exercise_id,),
            )


def reveal_hint(exercise_id: str, total_hints: int) -> int:
    with _connect() as conn:
        _ensure_row(conn, exercise_id)
        conn.execute(
            """UPDATE progress SET hints_revealed = MIN(hints_revealed + 1, ?),
               status = CASE status WHEN 'not_started' THEN 'in_progress' ELSE status END
               WHERE exercise_id = ?""",
            (total_hints, exercise_id),
        )
        row = conn.execute(
            "SELECT hints_revealed FROM progress WHERE exercise_id = ?", (exercise_id,)
        ).fetchone()
    return row["hints_revealed"]


def set_completed(exercise_id: str, completed: bool) -> None:
    with _connect() as conn:
        _ensure_row(conn, exercise_id)
        if completed:
            conn.execute(
                """UPDATE progress SET status = 'completed', completed_at = ?,
                   times_completed = times_completed + 1
                   WHERE exercise_id = ? AND status != 'completed'""",
                (_now(), exercise_id),
            )
        else:
            conn.execute(
                "UPDATE progress SET status = 'in_progress', completed_at = NULL WHERE exercise_id = ?",
                (exercise_id,),
            )


def reset(exercise_id: str) -> None:
    """Start an exercise over. times_completed is kept as history."""
    with _connect() as conn:
        _ensure_row(conn, exercise_id)
        conn.execute(
            """UPDATE progress SET status = 'not_started', hints_revealed = 0, attempts = 0,
               completed_at = NULL, last_result = NULL WHERE exercise_id = ?""",
            (exercise_id,),
        )
