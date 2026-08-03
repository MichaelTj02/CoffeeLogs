from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# max_length values mirror the column lengths in models.py, so an over-length string is a
# 422 here rather than a 500 from MySQL's STRICT_TRANS_TABLES.


class BrewAttemptBase(BaseModel):
    brewed_at: datetime | None = None
    dose_grams: float = Field(gt=0, le=1000)
    yield_grams: float = Field(gt=0, le=5000)
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


# The *Create schemas omit ids that come from the URL path on purpose — otherwise a client
# could POST to /methods/1/attempts with brew_method_id: 2.
class BrewAttemptCreate(BrewAttemptBase):
    pass


class BrewAttemptRead(BrewAttemptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brew_method_id: int
    brewed_at: datetime


class BrewMethodBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class BrewMethodCreate(BrewMethodBase):
    pass


class BrewMethodRead(BrewMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bean_id: int
    created_at: datetime
    attempts: list[BrewAttemptRead] = []


class BeanBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    roaster: str = Field(min_length=1, max_length=120)
    origin: str | None = Field(default=None, max_length=120)
    roast_date: date | None = None
    # float, not Decimal, despite the Numeric column: Pydantic v2 serializes Decimal to a
    # JSON *string* ("12.50"), which would force parseFloat across the frontend.
    price: float | None = Field(default=None, ge=0, le=9999.99)
    notes: str | None = None


class BeanCreate(BeanBase):
    pass


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_favourite: bool
    created_at: datetime


class BeanDetail(BeanRead):
    brew_methods: list[BrewMethodRead] = []


class FavouriteUpdate(BaseModel):
    is_favourite: bool
