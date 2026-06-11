from app.application.exceptions import NotFoundError
from app.domain.filters import BreachFilters
from app.infrastructure.persistence.models import BreachModel
from app.infrastructure.persistence.repositories import BreachRepository


class BreachQueryService:
    def __init__(self, repository: BreachRepository) -> None:
        self.repository = repository

    def get_by_name(self, name: str) -> BreachModel:
        breach = self.repository.get(name)
        if breach is None:
            raise NotFoundError(f"Breach '{name}' was not found.")
        return breach

    def list_breaches(
        self, filters: BreachFilters, *, page: int, page_size: int
    ) -> tuple[list[BreachModel], int]:
        return self.repository.list_filtered(filters, page=page, page_size=page_size)
