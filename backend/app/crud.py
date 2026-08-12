from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Bean, BrewAttempt, BrewMethod, User, UserSession, utcnow
from app.schemas import BeanCreate, BrewAttemptCreate, BrewMethodCreate
from app.security import SESSION_TTL, hash_password, hash_token, new_session_token


def list_beans(
    db: Session,
    user_id: int,
    limit: int | None = None,
    sort: Literal["favourites", "recent"] = "favourites",
) -> list[Bean]:
    order = (
        (Bean.created_at.desc(), Bean.id.desc())
        if sort == "recent"
        else (Bean.is_favourite.desc(), Bean.created_at.desc(), Bean.id.desc())
    )
    # brew_methods is not in BeanRead, but method_count reads it, so without the selectinload
    # serializing the list lazy-loads once per bean.
    stmt = (
        select(Bean)
        .options(selectinload(Bean.brew_methods))
        .where(Bean.user_id == user_id)
        .order_by(*order)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


# Not db.get(): a primary-key lookup cannot carry the ownership filter.
def get_bean(db: Session, user_id: int, bean_id: int) -> Bean | None:
    stmt = select(Bean).where(Bean.id == bean_id, Bean.user_id == user_id)
    return db.execute(stmt).scalars().first()


def get_bean_detail(db: Session, user_id: int, bean_id: int) -> Bean | None:
    # Chaining the selectinload keeps this to three queries instead of an N+1 across both
    # levels during serialization.
    stmt = (
        select(Bean)
        .options(selectinload(Bean.brew_methods).selectinload(BrewMethod.attempts))
        .where(Bean.id == bean_id, Bean.user_id == user_id)
    )
    return db.execute(stmt).scalars().first()


def create_bean(db: Session, user_id: int, data: BeanCreate) -> Bean:
    bean = Bean(user_id=user_id, **data.model_dump())
    db.add(bean)
    db.commit()
    db.refresh(bean)
    return bean


def set_bean_favourite(db: Session, bean: Bean, is_favourite: bool) -> Bean:
    bean.is_favourite = is_favourite
    db.commit()
    db.refresh(bean)
    return bean


# Takes the loaded object on purpose: the ORM cascade only fires for db.delete(obj), and a
# bulk query(...).delete() would bypass it.
def delete_bean(db: Session, bean: Bean) -> None:
    db.delete(bean)
    db.commit()


# bean_id is already ownership-checked by the caller.
def list_methods(db: Session, bean_id: int) -> list[BrewMethod]:
    stmt = (
        select(BrewMethod)
        .options(selectinload(BrewMethod.attempts))
        .where(BrewMethod.bean_id == bean_id)
        .order_by(BrewMethod.created_at, BrewMethod.id)
    )
    return list(db.execute(stmt).scalars().all())


def get_method(db: Session, user_id: int, method_id: int) -> BrewMethod | None:
    stmt = (
        select(BrewMethod)
        .join(BrewMethod.bean)
        .where(BrewMethod.id == method_id, Bean.user_id == user_id)
    )
    return db.execute(stmt).scalars().first()


# bean_id is already ownership-checked by the caller.
def find_method_by_name(db: Session, bean_id: int, name: str) -> BrewMethod | None:
    stmt = select(BrewMethod).where(BrewMethod.bean_id == bean_id, BrewMethod.name == name)
    return db.execute(stmt).scalars().first()


# bean_id is already ownership-checked by the caller.
def create_method(db: Session, bean_id: int, data: BrewMethodCreate) -> BrewMethod:
    method = BrewMethod(bean_id=bean_id, name=data.name)
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


def delete_method(db: Session, method: BrewMethod) -> None:
    db.delete(method)
    db.commit()


# method_id is already ownership-checked by the caller.
def list_attempts(db: Session, method_id: int) -> list[BrewAttempt]:
    stmt = (
        select(BrewAttempt)
        .where(BrewAttempt.brew_method_id == method_id)
        .order_by(BrewAttempt.brewed_at.desc(), BrewAttempt.id.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_attempt(db: Session, user_id: int, attempt_id: int) -> BrewAttempt | None:
    stmt = (
        select(BrewAttempt)
        .join(BrewAttempt.brew_method)
        .join(BrewMethod.bean)
        .where(BrewAttempt.id == attempt_id, Bean.user_id == user_id)
    )
    return db.execute(stmt).scalars().first()


# method_id is already ownership-checked by the caller.
def create_attempt(db: Session, method_id: int, data: BrewAttemptCreate) -> BrewAttempt:
    payload = data.model_dump()
    # A blank date input sends null; default it to today rather than rejecting.
    if payload.get("brewed_at") is None:
        payload.pop("brewed_at", None)
    attempt = BrewAttempt(brew_method_id=method_id, **payload)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def delete_attempt(db: Session, attempt: BrewAttempt) -> None:
    db.delete(attempt)
    db.commit()


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalars().first()


def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# The raw token is returned here and nowhere else — only its hash is stored, so it cannot be
# recovered afterwards.
def create_session(db: Session, user_id: int) -> tuple[UserSession, str]:
    token = new_session_token()
    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=utcnow() + SESSION_TTL,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, token


def get_session_by_token_hash(db: Session, token_hash: str) -> UserSession | None:
    stmt = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.token_hash == token_hash)
    )
    return db.execute(stmt).scalars().first()


def delete_session(db: Session, session: UserSession) -> None:
    db.delete(session)
    db.commit()


def delete_expired_sessions(db: Session, user_id: int) -> None:
    stmt = select(UserSession).where(
        UserSession.user_id == user_id, UserSession.expires_at <= utcnow()
    )
    for session in db.execute(stmt).scalars().all():
        db.delete(session)
    db.commit()
