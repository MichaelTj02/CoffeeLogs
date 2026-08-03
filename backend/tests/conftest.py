from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Bean, BrewAttempt, BrewMethod

# StaticPool plus check_same_thread=False keeps every session on one connection: TestClient
# runs endpoints on a worker thread, which would otherwise get its own empty in-memory DB.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# SQLite ignores foreign keys unless asked, so the cascades would silently pass untested.
@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(tables):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(tables):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_bean(db):
    def _make(**overrides):
        values = {"name": "Ethiopia Guji", "roaster": "Square Mile"}
        values.update(overrides)
        bean = Bean(**values)
        db.add(bean)
        db.commit()
        db.refresh(bean)
        return bean

    return _make


@pytest.fixture
def make_method(db):
    def _make(bean, **overrides):
        values = {"bean_id": bean.id, "name": "V60"}
        values.update(overrides)
        method = BrewMethod(**values)
        db.add(method)
        db.commit()
        db.refresh(method)
        return method

    return _make


@pytest.fixture
def make_attempt(db):
    def _make(method, **overrides):
        values = {
            "brew_method_id": method.id,
            "brewed_at": datetime(2026, 1, 1, 8, 0, 0),
            "dose_grams": 18.0,
            "yield_grams": 300.0,
        }
        values.update(overrides)
        attempt = BrewAttempt(**values)
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    return _make
