import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# backend/workspace/booking/db.py -> backend/data/booking.db
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "booking.db"
DB_PATH = Path(os.environ.get("BOOKING_DB_PATH", DEFAULT_DB_PATH))


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
