"""Engine, session factory, and the declarative base."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DEFAULT_DATABASE_URL = (
    "mysql+pymysql://coffeelogs:coffeelogs@localhost:3306/coffeelogs?charset=utf8mb4"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# create_engine() does not connect — SQLAlchemy pools are lazy, and the first TCP
# connection happens on first Session use. That is what lets the test suite (and a bare
# `import app.main`) run on a machine with no MySQL at all.
#
# pool_pre_ping guards MySQL's wait_timeout: without it, a connection that the server
# closed while idle surfaces later as `OperationalError 2013: Lost connection`.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
