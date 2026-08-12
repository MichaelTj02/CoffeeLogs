from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_bean_or_404, get_current_user, get_method_or_404
from app.models import User
from app.schemas import BrewMethodCreate, BrewMethodRead

router = APIRouter(tags=["brew methods"])


@router.get("/beans/{bean_id}/methods", response_model=list[BrewMethodRead])
def list_methods(
    bean_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_bean_or_404(db, user.id, bean_id)
    return crud.list_methods(db, bean_id)


@router.post(
    "/beans/{bean_id}/methods",
    response_model=BrewMethodRead,
    status_code=status.HTTP_201_CREATED,
)
def create_method(
    bean_id: int,
    data: BrewMethodCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_bean_or_404(db, user.id, bean_id)
    # Checked up front so a duplicate is a 409 rather than an IntegrityError 500; the unique
    # constraint is still the real guarantee.
    if crud.find_method_by_name(db, bean_id, data.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This bean already has a '{data.name}' method",
        )
    return crud.create_method(db, bean_id, data)


@router.delete(
    "/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_method(
    method_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    method = get_method_or_404(db, user.id, method_id)
    crud.delete_method(db, method)
