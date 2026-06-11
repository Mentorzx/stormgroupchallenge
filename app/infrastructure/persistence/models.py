from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BreachModel(Base):
    __tablename__ = "breaches"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    breach_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    added_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modified_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pwn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_classes: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list
    )
    data_classes_normalized: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fabricated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_retired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_spam_list: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_malware: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_payload: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


Index("ix_breaches_lower_domain", func.lower(BreachModel.domain))
Index("ix_breaches_breach_date", BreachModel.breach_date)
Index("ix_breaches_added_date", BreachModel.added_date)
Index("ix_breaches_pwn_count", BreachModel.pwn_count)
Index("ix_breaches_is_verified", BreachModel.is_verified)
Index("ix_breaches_is_sensitive", BreachModel.is_sensitive)
Index("ix_breaches_is_spam_list", BreachModel.is_spam_list)
Index(
    "ix_breaches_data_classes_normalized_gin",
    BreachModel.data_classes_normalized,
    postgresql_using="gin",
)
