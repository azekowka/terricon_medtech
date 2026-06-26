"""Pytest fixtures. Forces a throwaway SQLite DB before the app imports settings."""
import os
import tempfile

# Must be set before importing app.* (engine is built from settings at import time).
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest

from app.db import SessionLocal, init_db
from app.seeding import seed_database


@pytest.fixture(scope="session")
def seeded_db():
    init_db()
    db = SessionLocal()
    seed_database(db, include_live=False)
    yield db
    db.close()
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
