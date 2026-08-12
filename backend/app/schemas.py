import re
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# max_length values mirror the column lengths in models.py, so an over-length string is a
# 422 here rather than a 500 from MySQL's STRICT_TRANS_TABLES.


# created_at columns are naive DATETIME(6) holding UTC; the wire contract is UTC with an
# explicit offset. brewed_at is a plain calendar date and is deliberately not covered here.
# check_fields=False is required because the mixin itself declares no created_at field.
class UTCAwareOut(BaseModel):
    @field_serializer("created_at", check_fields=False)
    def _serialize_utc(self, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC)


class BrewAttemptBase(BaseModel):
    # A calendar date, not an instant: the day you brewed is the same day everywhere, so
    # there is no timezone to convert and no time of day worth recording.
    brewed_at: date | None = None
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
    brewed_at: date


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


_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class UserCredentials(BaseModel):
    email: str = Field(max_length=255)
    # Never trimmed, unlike the email: leading or trailing whitespace is part of a password.
    # The 128 cap bounds argon2's hashing cost; it mirrors no column length.
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="after")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        # Shape-checked here rather than via Field(pattern=...), which runs before this
        # lowercasing and would reject A@B.COM. Stripping matters because an address
        # registered with stray whitespace could never be logged into.
        email = value.strip().lower()
        if _EMAIL_RE.fullmatch(email) is None:
            raise ValueError("Not a valid email address")
        return email


# Login deliberately inherits the min_length=1 password instead: an existing password shorter
# than this must fail as a 401, not a 422.
class UserRegister(UserCredentials):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UTCAwareOut):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
