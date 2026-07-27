"""Shared 404 lookup helpers used across the routers."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.models import Bean, BrewAttempt, BrewMethod


def get_bean_or_404(db: Session, bean_id: int) -> Bean:
    bean = crud.get_bean(db, bean_id)
    if bean is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Bean {bean_id} not found"
        )
    return bean


def get_method_or_404(db: Session, method_id: int) -> BrewMethod:
    method = crud.get_method(db, method_id)
    if method is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Brew method {method_id} not found"
        )
    return method


def get_attempt_or_404(db: Session, attempt_id: int) -> BrewAttempt:
    attempt = crud.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Brew attempt {attempt_id} not found"
        )
    return attempt
