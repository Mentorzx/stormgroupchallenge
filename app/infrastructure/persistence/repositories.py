from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.domain.filters import BreachFilters
from app.infrastructure.persistence.models import BreachModel


class BreachRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, name: str) -> BreachModel | None:
        return self.session.get(BreachModel, name)

    def count(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(BreachModel)) or 0)

    def existing_names(self, names: Sequence[str]) -> set[str]:
        if not names:
            return set()
        rows = self.session.scalars(
            select(BreachModel.name).where(BreachModel.name.in_(names))
        ).all()
        return set(rows)

    def upsert_many(self, rows: list[dict]) -> None:
        if not rows:
            return

        now = datetime.now(UTC)
        prepared: list[dict] = []
        for row in rows:
            value = dict(row)
            value.setdefault("created_at", now)
            value["updated_at"] = now
            prepared.append(value)

        dialect = self.session.bind.dialect.name if self.session.bind is not None else ""

        if dialect == "postgresql":
            stmt = postgres_insert(BreachModel).values(prepared)
            update_columns = {
                column.name: getattr(stmt.excluded, column.name)
                for column in BreachModel.__table__.columns
                if column.name not in {"name", "created_at"}
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[BreachModel.name], set_=update_columns
            )
            self.session.execute(stmt)
            return

        if dialect == "sqlite":
            stmt = sqlite_insert(BreachModel).values(prepared)
            update_columns = {
                column.name: getattr(stmt.excluded, column.name)
                for column in BreachModel.__table__.columns
                if column.name not in {"name", "created_at"}
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[BreachModel.name], set_=update_columns
            )
            self.session.execute(stmt)
            return

        for row in prepared:
            existing = self.get(row["name"])
            if existing:
                for key, value in row.items():
                    if key not in {"name", "created_at"}:
                        setattr(existing, key, value)
            else:
                self.session.add(BreachModel(**row))

    def list_filtered(
        self, filters: BreachFilters, *, page: int, page_size: int
    ) -> tuple[list[BreachModel], int]:
        stmt = self._base_filtered_select(filters).order_by(BreachModel.name.asc())
        candidates = list(self.session.scalars(stmt).all())

        if filters.data_class:
            wanted = filters.data_class.strip().lower()
            candidates = [
                breach
                for breach in candidates
                if any(wanted == item.strip().lower() for item in (breach.data_classes or []))
            ]

        total = len(candidates)
        start = (page - 1) * page_size
        end = start + page_size
        return candidates[start:end], total

    def _base_filtered_select(self, filters: BreachFilters) -> Select[tuple[BreachModel]]:
        stmt = select(BreachModel)

        if filters.name is not None:
            stmt = stmt.where(BreachModel.name == filters.name)
        if filters.domain is not None:
            stmt = stmt.where(
                BreachModel.domain.is_not(None),
                func.lower(BreachModel.domain).contains(filters.domain.lower(), autoescape=True),
            )
        if filters.breach_date_from is not None:
            stmt = stmt.where(BreachModel.breach_date >= filters.breach_date_from)
        if filters.breach_date_to is not None:
            stmt = stmt.where(BreachModel.breach_date <= filters.breach_date_to)
        if filters.added_date_from is not None:
            stmt = stmt.where(BreachModel.added_date >= filters.added_date_from)
        if filters.added_date_to is not None:
            stmt = stmt.where(BreachModel.added_date <= filters.added_date_to)
        if filters.min_pwn_count is not None:
            stmt = stmt.where(BreachModel.pwn_count >= filters.min_pwn_count)
        if filters.max_pwn_count is not None:
            stmt = stmt.where(BreachModel.pwn_count <= filters.max_pwn_count)
        if filters.is_verified is not None:
            stmt = stmt.where(BreachModel.is_verified.is_(filters.is_verified))
        if filters.is_sensitive is not None:
            stmt = stmt.where(BreachModel.is_sensitive.is_(filters.is_sensitive))
        if filters.is_spam_list is not None:
            stmt = stmt.where(BreachModel.is_spam_list.is_(filters.is_spam_list))

        return stmt
