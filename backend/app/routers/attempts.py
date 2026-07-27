"""Brew attempt endpoints — the individual brews under one method."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_attempt_or_404, get_method_or_404
from app.schemas import BrewAttemptCreate, BrewAttemptRead

router = APIRouter(tags=["brew attempts"])


@router.get("/methods/{method_id}/attempts", response_model=list[BrewAttemptRead])
def list_attempts(method_id: int, db: Session = Depends(get_db)):
    """Newest first."""
    get_method_or_404(db, method_id)
    return crud.list_attempts(db, method_id)


@router.post(
    "/methods/{method_id}/attempts",
    response_model=BrewAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_attempt(method_id: int, data: BrewAttemptCreate, db: Session = Depends(get_db)):
    get_method_or_404(db, method_id)
    return crud.create_attempt(db, method_id, data)


@router.delete(
    "/attempts/{attempt_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_attempt(attempt_id: int, db: Session = Depends(get_db)) -> None:
    attempt = get_attempt_or_404(db, attempt_id)
    crud.delete_attempt(db, attempt)
