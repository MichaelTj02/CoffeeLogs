from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Bean, BrewAttempt, BrewMethod
from app.schemas import BeanCreate, BrewAttemptCreate, BrewMethodCreate


def list_beans(db: Session, limit: int | None = None) -> list[Bean]:
    stmt = (
        select(Bean)
        .options(selectinload(Bean.brew_methods))
        .order_by(Bean.is_favourite.desc(), Bean.created_at.desc(), Bean.id.desc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_bean(db: Session, bean_id: int) -> Bean | None:
    return db.get(Bean, bean_id)


def get_bean_detail(db: Session, bean_id: int) -> Bean | None:
    # Chaining the selectinload keeps this to three queries instead of an N+1 across both
    # levels during serialization.
    stmt = (
        select(Bean)
        .options(selectinload(Bean.brew_methods).selectinload(BrewMethod.attempts))
        .where(Bean.id == bean_id)
    )
    return db.execute(stmt).scalars().first()


def create_bean(db: Session, data: BeanCreate) -> Bean:
    bean = Bean(**data.model_dump())
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


def list_methods(db: Session, bean_id: int) -> list[BrewMethod]:
    stmt = (
        select(BrewMethod)
        .options(selectinload(BrewMethod.attempts))
        .where(BrewMethod.bean_id == bean_id)
        .order_by(BrewMethod.created_at, BrewMethod.id)
    )
    return list(db.execute(stmt).scalars().all())


def get_method(db: Session, method_id: int) -> BrewMethod | None:
    return db.get(BrewMethod, method_id)


def find_method_by_name(db: Session, bean_id: int, name: str) -> BrewMethod | None:
    stmt = select(BrewMethod).where(BrewMethod.bean_id == bean_id, BrewMethod.name == name)
    return db.execute(stmt).scalars().first()


def create_method(db: Session, bean_id: int, data: BrewMethodCreate) -> BrewMethod:
    method = BrewMethod(bean_id=bean_id, name=data.name)
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


def delete_method(db: Session, method: BrewMethod) -> None:
    db.delete(method)
    db.commit()


def list_attempts(db: Session, method_id: int) -> list[BrewAttempt]:
    stmt = (
        select(BrewAttempt)
        .where(BrewAttempt.brew_method_id == method_id)
        .order_by(BrewAttempt.brewed_at.desc(), BrewAttempt.id.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_attempt(db: Session, attempt_id: int) -> BrewAttempt | None:
    return db.get(BrewAttempt, attempt_id)


def create_attempt(db: Session, method_id: int, data: BrewAttemptCreate) -> BrewAttempt:
    payload = data.model_dump()
    # A blank datetime-local input sends null; default it to now rather than rejecting.
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
