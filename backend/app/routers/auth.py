from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import UserCredentials, UserRead, UserRegister
from app.security import (
    COOKIE_NAME,
    SESSION_TTL,
    burn_dummy_verification,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DUPLICATE_EMAIL_DETAIL = "That email is already registered"
BAD_CREDENTIALS_DETAIL = "Incorrect email or password"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
        # Hardcoded for localhost over http; this becomes env-driven if the API is deployed.
        secure=False,
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL_DETAIL)
    try:
        user = crud.create_user(db, data.email, data.password)
    except IntegrityError:
        # Backstop for two registrations of the same email racing past the check above; the
        # unique index is the real guarantee.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL_DETAIL
        ) from None
    _, token = crud.create_session(db, user.id)
    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserRead)
def login(
    data: UserCredentials,
    response: Response,
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, data.email)
    if user is None:
        # There is no hash to check, so answer at the same speed as a wrong password rather
        # than revealing that the address is unregistered.
        burn_dummy_verification()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=BAD_CREDENTIALS_DETAIL
        )
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=BAD_CREDENTIALS_DETAIL
        )

    crud.delete_expired_sessions(db, user.id)
    if token is not None:
        presented = crud.get_session_by_token_hash(db, hash_token(token))
        if presented is not None:
            crud.delete_session(db, presented)

    _, new_token = crud.create_session(db, user.id)
    _set_session_cookie(response, new_token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> None:
    # Read the cookie directly rather than through get_current_user: logging out twice, or
    # with an expired cookie, must still succeed.
    if token is not None:
        session = crud.get_session_by_token_hash(db, hash_token(token))
        if session is not None:
            crud.delete_session(db, session)
    # The attributes must mirror _set_session_cookie — a path mismatch leaves the browser's
    # cookie alive and the clear silently does nothing.
    response.delete_cookie(COOKIE_NAME, path="/", samesite="lax", httponly=True)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
