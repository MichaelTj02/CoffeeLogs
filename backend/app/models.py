"""SQLAlchemy models: beans --< brew_methods --< brew_attempts."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Plain DateTime compiles to MySQL DATETIME(0) — whole seconds, with sub-second precision
# silently discarded. Two attempts logged in the same second would then tie under
# `ORDER BY brewed_at DESC`. The variant keeps microseconds on MySQL and is a no-op
# everywhere else.
UTC_DATETIME = DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql")


def _utcnow() -> datetime:
    """Naive UTC now. MySQL DATETIME carries no timezone, so we store naive UTC."""
    return datetime.now(UTC).replace(tzinfo=None)


class Bean(Base):
    __tablename__ = "beans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Every String needs an explicit length or MySQL raises
    # `CompileError: VARCHAR requires a length`.
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    roaster: Mapped[str] = mapped_column(String(120), nullable=False)
    origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Date, not DateTime: a roast date has no meaningful time-of-day, and DateTime would
    # make <input type="date"> fabricate T00:00:00 and invite timezone-shift bugs.
    roast_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Numeric, not Float: money in binary float rounds wrong (19.99 -> 19.989999...).
    price: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favourite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", index=True
    )
    # No server_default: MySQL requires CURRENT_TIMESTAMP's precision to match the
    # column's, so `DATETIME(6) DEFAULT now()` is error 1067. The Python-side default
    # covers every insert and populates the value on the instance immediately, so a POST
    # response carries created_at without a second round-trip.
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, default=_utcnow)

    brew_methods: Mapped[list["BrewMethod"]] = relationship(
        back_populates="bean",
        cascade="all, delete-orphan",
        order_by="BrewMethod.created_at",
    )

    def __repr__(self) -> str:
        return f"<Bean id={self.id} name={self.name!r}>"


class BrewMethod(Base):
    __tablename__ = "brew_methods"
    # One "V60" per bean. The route turns a violation into a 409 rather than letting a raw
    # IntegrityError become a 500.
    __table_args__ = (UniqueConstraint("bean_id", "name", name="uq_brew_method_bean_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bean_id: Mapped[int] = mapped_column(
        ForeignKey("beans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    # No server_default: MySQL requires CURRENT_TIMESTAMP's precision to match the
    # column's, so `DATETIME(6) DEFAULT now()` is error 1067. The Python-side default
    # covers every insert and populates the value on the instance immediately, so a POST
    # response carries created_at without a second round-trip.
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, default=_utcnow)

    bean: Mapped[Bean] = relationship(back_populates="brew_methods")
    attempts: Mapped[list["BrewAttempt"]] = relationship(
        back_populates="brew_method",
        cascade="all, delete-orphan",
        order_by="BrewAttempt.brewed_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<BrewMethod id={self.id} name={self.name!r} bean_id={self.bean_id}>"


class BrewAttempt(Base):
    __tablename__ = "brew_attempts"
    # MySQL 8.0.16+ actually enforces CHECK constraints (5.7 parsed and ignored them), and
    # SQLite enforces them too, so this backs up the Pydantic validation at the database.
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_brew_attempt_rating"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brew_method_id: Mapped[int] = mapped_column(
        ForeignKey("brew_methods.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # DateTime, not Date: you brew several times a day, so time-of-day is what separates
    # one attempt from the next.
    brewed_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, default=_utcnow)
    # Float is right here — grams are measurements, not currency.
    dose_grams: Mapped[float] = mapped_column(Float, nullable=False)
    yield_grams: Mapped[float] = mapped_column(Float, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brew_method: Mapped[BrewMethod] = relationship(back_populates="attempts")

    def __repr__(self) -> str:
        return f"<BrewAttempt id={self.id} brew_method_id={self.brew_method_id}>"
