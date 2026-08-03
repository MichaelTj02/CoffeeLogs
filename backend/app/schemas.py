from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# max_length values mirror the column lengths in models.py, so an over-length string is a
# 422 here rather than a 500 from MySQL's STRICT_TRANS_TABLES.


# Columns are naive DATETIME(6) holding UTC; the wire contract is UTC with an explicit
# offset. check_fields lets one mixin cover the differently-named field on each Read schema.
class UTCAwareOut(BaseModel):
    @field_serializer("created_at", "brewed_at", check_fields=False)
    def _serialize_utc(self, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC)


class BrewAttemptBase(BaseModel):
    brewed_at: datetime | None = None
    dose_grams: float = Field(gt=0, le=1000)
    yield_grams: float = Field(gt=0, le=5000)
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None

    # Naive input is taken as UTC rather than rejected — clients other than our frontend
    # may omit the offset.
    @field_validator("brewed_at", mode="after")
    @classmethod
    def _to_naive_utc(cls, value: datetime | None) -> datetime | None:
        if value is None or value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)


# The *Create schemas omit ids that come from the URL path on purpose — otherwise a client
# could POST to /methods/1/attempts with brew_method_id: 2.
class BrewAttemptCreate(BrewAttemptBase):
    pass


class BrewAttemptRead(BrewAttemptBase, UTCAwareOut):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brew_method_id: int
    brewed_at: datetime


class BrewMethodBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class BrewMethodCreate(BrewMethodBase):
    pass


class BrewMethodRead(BrewMethodBase, UTCAwareOut):
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


class BeanRead(BeanBase, UTCAwareOut):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_favourite: bool
    created_at: datetime
    method_count: int


class BeanDetail(BeanRead):
    brew_methods: list[BrewMethodRead] = []


class FavouriteUpdate(BaseModel):
    is_favourite: bool
