from datetime import datetime, timedelta

from conftest import PASSWORD
from sqlalchemy import func, select

from app import crud
from app.models import UserSession, utcnow
from app.security import COOKIE_NAME, hash_token


def add_expired_session(db, user_id, token):
    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=utcnow() - timedelta(days=1),
    )
    db.add(session)
    db.commit()
    return session


def count_sessions(db, user_id):
    stmt = select(func.count()).select_from(UserSession).where(UserSession.user_id == user_id)
    return db.execute(stmt).scalar_one()


def test_register_returns_201_with_the_new_user(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "new@example.com", "password": PASSWORD}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["email"] == "new@example.com"
    # Nothing else may leak: no password_hash, and no user_id on any response schema.
    assert set(body) == {"id", "email", "created_at"}
    assert body["created_at"].endswith("Z") or body["created_at"].endswith("+00:00")
    assert datetime.fromisoformat(body["created_at"]).utcoffset() == timedelta(0)


def test_register_sets_a_session_cookie(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "new@example.com", "password": PASSWORD}
    )

    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "httponly" in cookie
    assert "path=/" in cookie
    assert "samesite=lax" in cookie


def test_register_logs_the_new_user_in(anon_client):
    anon_client.post("/auth/register", json={"email": "new@example.com", "password": PASSWORD})

    response = anon_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


def test_register_normalizes_the_email(anon_client, db):
    response = anon_client.post(
        "/auth/register", json={"email": "  A@B.COM ", "password": PASSWORD}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "a@b.com"
    db.expire_all()
    assert crud.get_user_by_email(db, "a@b.com") is not None


def test_register_duplicate_email_is_409(anon_client, user):
    response = anon_client.post(
        "/auth/register", json={"email": user.email, "password": PASSWORD}
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_email_is_409_even_if_the_check_misses(anon_client, user, monkeypatch):
    # Blinding the pre-check simulates two registrations racing past it; the unique index is
    # the real guarantee and the IntegrityError backstop is what turns it into a 409.
    monkeypatch.setattr(crud, "get_user_by_email", lambda *args, **kwargs: None)
    create_user = crud.create_user
    attempted = []

    def spy_create_user(db, email, password):
        attempted.append(email)
        return create_user(db, email, password)

    monkeypatch.setattr(crud, "create_user", spy_create_user)

    response = anon_client.post(
        "/auth/register", json={"email": user.email, "password": PASSWORD}
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]
    # Without this the test would still pass through the pre-check if the patch stopped working.
    assert attempted == [user.email]


def test_register_rejects_a_short_password(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "new@example.com", "password": "sevench"}
    )

    assert response.status_code == 422


def test_register_rejects_a_malformed_email(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "not-an-email", "password": PASSWORD}
    )

    assert response.status_code == 422


def test_register_rejects_an_overlong_email(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "a" * 250 + "@example.com", "password": PASSWORD}
    )

    assert response.status_code == 422


def test_register_rejects_an_overlong_password(anon_client):
    response = anon_client.post(
        "/auth/register", json={"email": "new@example.com", "password": "x" * 129}
    )

    assert response.status_code == 422


def test_login_returns_200_and_sets_a_session_cookie(anon_client, user):
    response = anon_client.post("/auth/login", json={"email": user.email, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["id"] == user.id
    assert "httponly" in response.headers["set-cookie"].lower()
    assert anon_client.get("/auth/me").status_code == 200


def test_login_with_the_wrong_password_is_401(anon_client, user):
    response = anon_client.post("/auth/login", json={"email": user.email, "password": "wrong-pass"})

    assert response.status_code == 401


def test_login_hides_whether_the_email_exists(anon_client, user):
    wrong_password = anon_client.post(
        "/auth/login", json={"email": user.email, "password": "wrong-pass"}
    )
    unknown_email = anon_client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "wrong-pass"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]
    assert wrong_password.json()["detail"] == "Incorrect email or password"


def test_login_ignores_email_case_and_surrounding_whitespace(anon_client, user):
    response = anon_client.post(
        "/auth/login", json={"email": "  BREWER@EXAMPLE.COM  ", "password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["id"] == user.id


def test_login_does_not_apply_the_register_password_minimum(anon_client, user):
    # A password shorter than register's minimum must fail authentication, not validation.
    response = anon_client.post("/auth/login", json={"email": user.email, "password": "x"})

    assert response.status_code == 401


def test_login_deletes_that_users_expired_sessions(anon_client, db, user):
    add_expired_session(db, user.id, "stale-token")

    response = anon_client.post("/auth/login", json={"email": user.email, "password": PASSWORD})

    assert response.status_code == 200
    db.expire_all()
    assert crud.get_session_by_token_hash(db, hash_token("stale-token")) is None
    assert count_sessions(db, user.id) == 1


def test_logout_returns_204_with_no_body(client):
    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""


def test_logout_clears_the_cookie(client):
    cookie = client.post("/auth/logout").headers["set-cookie"].lower()

    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "max-age=0" in cookie
    # The attributes must mirror the set: a path mismatch leaves the browser's cookie alive.
    assert "path=/" in cookie
    assert "samesite=lax" in cookie
    assert "httponly" in cookie


def test_logout_deletes_the_session_row(client, db):
    token = client.cookies[COOKIE_NAME]

    client.post("/auth/logout")

    db.expire_all()
    assert crud.get_session_by_token_hash(db, hash_token(token)) is None
    client.cookies.set(COOKIE_NAME, token)
    assert client.get("/auth/me").status_code == 401


def test_logout_is_idempotent(client):
    assert client.post("/auth/logout").status_code == 204
    assert client.post("/auth/logout").status_code == 204


def test_me_returns_the_signed_in_user(client, user):
    response = client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["email"] == user.email
    assert set(body) == {"id", "email", "created_at"}


def test_me_is_401_when_anonymous(anon_client):
    assert anon_client.get("/auth/me").status_code == 401


def test_an_expired_session_is_401_and_its_row_is_deleted(anon_client, db, user):
    add_expired_session(db, user.id, "stale-token")
    anon_client.cookies.set(COOKIE_NAME, "stale-token")

    assert anon_client.get("/auth/me").status_code == 401

    db.expire_all()
    assert count_sessions(db, user.id) == 0
