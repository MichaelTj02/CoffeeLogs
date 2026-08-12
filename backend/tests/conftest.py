from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud
from app.database import Base, get_db
from app.main import app
from app.models import Bean, BrewAttempt, BrewMethod, User
from app.security import COOKIE_NAME, hash_password

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

PASSWORD = "brewed-strong-2026"
# argon2 costs 50-100ms per hash by design, so every test user shares one hash computed at
# import rather than paying that per fixture.
PASSWORD_HASH = hash_password(PASSWORD)


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


# Installed once per test so several clients can share it; each client owning its own
# override would have them fighting over app.dependency_overrides.
@pytest.fixture
def db_override(tables):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def _make(email="brewer@example.com", **overrides):
        values = {"email": email, "password_hash": PASSWORD_HASH}
        values.update(overrides)
        user = User(**values)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def make_client(db, db_override):
    def _make(user):
        # The session row goes in directly: a login round-trip would re-verify the argon2
        # hash on every test.
        _, token = crud.create_session(db, user.id)
        client = TestClient(app)
        client.cookies.set(COOKIE_NAME, token)
        return client

    return _make


@pytest.fixture
def client(make_client, user):
    return make_client(user)


@pytest.fixture
def anon_client(db_override):
    return TestClient(app)


@pytest.fixture
def make_bean(db, user):
    def _make(**overrides):
        values = {"name": "Ethiopia Guji", "roaster": "Square Mile", "user_id": user.id}
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
            "brewed_at": date(2026, 1, 1),
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
