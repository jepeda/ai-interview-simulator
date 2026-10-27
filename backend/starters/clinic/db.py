import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# backend/workspace/clinic/db.py -> backend/data/clinic.db
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "clinic.db"
DB_PATH = Path(os.environ.get("CLINIC_DB_PATH", DEFAULT_DB_PATH))


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    # SQLite connections are thread-bound by default; FastAPI runs sync endpoints in a threadpool.
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
