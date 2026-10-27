"""Clinic API - a small (deliberately buggy) mental-health practice backend.

Layout (mirrors a typical FastAPI service):
  main.py              app factory, lifespan (create tables + seed)
  db.py                SQLAlchemy engine/session + get_db dependency
  models.py            ORM models (tables)
  schemas.py           Pydantic request/response models (the API contract)
  repository.py        query functions
  services/            business logic (eligibility rules, appointment views, cache)
  routers/             HTTP endpoints
  seed.py              demo data
"""
