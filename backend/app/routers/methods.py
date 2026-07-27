"""Brew method endpoints.

Methods are created under their bean but addressed by their own id afterwards — ids are
globally unique, so nesting deletes three levels deep would add path noise and redundant
validation for nothing.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_bean_or_404, get_method_or_404
from app.schemas import BrewMethodCreate, BrewMethodRead

router = APIRouter(tags=["brew methods"])


@router.get("/beans/{bean_id}/methods", response_model=list[BrewMethodRead])
def list_methods(bean_id: int, db: Session = Depends(get_db)):
    get_bean_or_404(db, bean_id)
    return crud.list_methods(db, bean_id)


@router.post(
    "/beans/{bean_id}/methods",
    response_model=BrewMethodRead,
    status_code=status.HTTP_201_CREATED,
)
def create_method(bean_id: int, data: BrewMethodCreate, db: Session = Depends(get_db)):
    get_bean_or_404(db, bean_id)
    # Checked up front so a duplicate is a clean 409 rather than an IntegrityError 500.
    # The unique constraint is still the real guarantee.
    if crud.find_method_by_name(db, bean_id, data.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This bean already has a '{data.name}' method",
        )
    return crud.create_method(db, bean_id, data)


@router.delete(
    "/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_method(method_id: int, db: Session = Depends(get_db)) -> None:
    """Cascades to this method's attempts."""
    method = get_method_or_404(db, method_id)
    crud.delete_method(db, method)
