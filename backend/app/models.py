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

# Plain DateTime compiles to MySQL DATETIME(0), silently truncating sub-second precision,
# which makes same-second attempts tie when ordered by time.
UTC_DATETIME = DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Bean(Base):
    __tablename__ = "beans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Every String needs an explicit length or MySQL raises "VARCHAR requires a length".
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    roaster: Mapped[str] = mapped_column(String(120), nullable=False)
    origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    roast_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favourite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", index=True
    )
    # No server_default: MySQL requires CURRENT_TIMESTAMP's precision to match the column's,
    # so `DATETIME(6) DEFAULT now()` is error 1067.
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, default=_utcnow)

    brew_methods: Mapped[list["BrewMethod"]] = relationship(
        back_populates="bean",
        cascade="all, delete-orphan",
        order_by="BrewMethod.created_at",
    )

    @property
    def method_count(self) -> int:
        return len(self.brew_methods)

    def __repr__(self) -> str:
        return f"<Bean id={self.id} name={self.name!r}>"


class BrewMethod(Base):
    __tablename__ = "brew_methods"
    __table_args__ = (UniqueConstraint("bean_id", "name", name="uq_brew_method_bean_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bean_id: Mapped[int] = mapped_column(
        ForeignKey("beans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
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
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_brew_attempt_rating"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brew_method_id: Mapped[int] = mapped_column(
        ForeignKey("brew_methods.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brewed_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, default=_utcnow)
    dose_grams: Mapped[float] = mapped_column(Float, nullable=False)
    yield_grams: Mapped[float] = mapped_column(Float, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brew_method: Mapped[BrewMethod] = relationship(back_populates="attempts")

    def __repr__(self) -> str:
        return f"<BrewAttempt id={self.id} brew_method_id={self.brew_method_id}>"
