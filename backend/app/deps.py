from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Bean, BrewAttempt, BrewMethod, User, utcnow
from app.security import COOKIE_NAME, hash_token


def get_current_user(
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    # default=None is load-bearing: without it FastAPI treats the cookie as required and an
    # anonymous request is rejected with a 422 before this body ever runs.
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session = crud.get_session_by_token_hash(db, hash_token(token))
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if session.expires_at <= utcnow():
        crud.delete_session(db, session)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return session.user


# A bean owned by someone else is a 404, not a 403: 403 would confirm the id exists.
def get_bean_or_404(db: Session, user_id: int, bean_id: int) -> Bean:
    bean = crud.get_bean(db, user_id, bean_id)
    if bean is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Bean {bean_id} not found"
        )
    return bean


def get_method_or_404(db: Session, user_id: int, method_id: int) -> BrewMethod:
    method = crud.get_method(db, user_id, method_id)
    if method is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Brew method {method_id} not found"
        )
    return method


def get_attempt_or_404(db: Session, user_id: int, attempt_id: int) -> BrewAttempt:
    attempt = crud.get_attempt(db, user_id, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Brew attempt {attempt_id} not found"
        )
    return attempt
