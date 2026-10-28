"""Helpers for the trainer's tests: read a session's log and state."""

import json

from trainer import interview


def events(session_id: str) -> list[dict]:
    return interview._events(session_id)


def kinds(session_id: str) -> list[str]:
    return [e["kind"] for e in events(session_id)]


def state(sandbox: bool = False) -> dict:
    path = interview.SANDBOX_STATE_PATH if sandbox else interview.STATE_PATH
    return json.loads(path.read_text(encoding="utf-8"))
