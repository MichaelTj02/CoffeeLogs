"""Pydantic v2 request/response models.

max_length values mirror the column lengths in models.py. MySQL runs in
STRICT_TRANS_TABLES and errors on over-length strings, so validating here turns what would
be a 500 into a clean 422.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- brew attempts


class BrewAttemptBase(BaseModel):
    brewed_at: datetime | None = None
    dose_grams: float = Field(gt=0, le=1000)
    yield_grams: float = Field(gt=0, le=5000)
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class BrewAttemptCreate(BrewAttemptBase):
    """No brew_method_id — it comes from the URL path.

    Accepting it in the body would let a client POST to /methods/1/attempts with
    brew_method_id: 2 and create an inconsistency.
    """


class BrewAttemptRead(BrewAttemptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brew_method_id: int
    brewed_at: datetime


# ---------------------------------------------------------------------------- brew methods


class BrewMethodBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class BrewMethodCreate(BrewMethodBase):
    """No bean_id — it comes from the URL path."""


class BrewMethodRead(BrewMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bean_id: int
    created_at: datetime
    attempts: list[BrewAttemptRead] = []


# ---------------------------------------------------------------------------------- beans


class BeanBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    roaster: str = Field(min_length=1, max_length=120)
    origin: str | None = Field(default=None, max_length=120)
    roast_date: date | None = None
    # float, not Decimal: Pydantic v2 serializes Decimal to a JSON *string* ("12.50"),
    # which would force parseFloat across the frontend. The column stays DECIMAL(6,2), so
    # storage is still exact — only the wire format changes.
    price: float | None = Field(default=None, ge=0, le=9999.99)
    notes: str | None = None


class BeanCreate(BeanBase):
    """Deliberately cannot set id, is_favourite, or created_at."""


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_favourite: bool
    created_at: datetime


class BeanDetail(BeanRead):
    """Bean with its methods, each carrying its own attempts."""

    brew_methods: list[BrewMethodRead] = []


class FavouriteUpdate(BaseModel):
    is_favourite: bool
