from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_bean_or_404
from app.schemas import BeanCreate, BeanDetail, BeanRead, FavouriteUpdate

router = APIRouter(prefix="/beans", tags=["beans"])


@router.get("", response_model=list[BeanRead])
def list_beans(
    limit: int | None = Query(default=None, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.list_beans(db, limit=limit)


@router.post("", response_model=BeanRead, status_code=status.HTTP_201_CREATED)
def create_bean(data: BeanCreate, db: Session = Depends(get_db)):
    return crud.create_bean(db, data)


@router.get("/{bean_id}", response_model=BeanDetail)
def get_bean(bean_id: int, db: Session = Depends(get_db)):
    get_bean_or_404(db, bean_id)
    return crud.get_bean_detail(db, bean_id)


@router.patch("/{bean_id}/favourite", response_model=BeanRead)
def set_favourite(bean_id: int, data: FavouriteUpdate, db: Session = Depends(get_db)):
    bean = get_bean_or_404(db, bean_id)
    return crud.set_bean_favourite(db, bean, data.is_favourite)


# No response_model and a None return: a 204 with a body is a protocol violation.
@router.delete("/{bean_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_bean(bean_id: int, db: Session = Depends(get_db)) -> None:
    bean = get_bean_or_404(db, bean_id)
    crud.delete_bean(db, bean)
