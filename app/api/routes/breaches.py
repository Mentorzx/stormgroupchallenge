from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import Settings, get_db, get_settings
from app.application.services.breach_query_service import BreachQueryService
from app.application.validators import (
    parse_bool,
    parse_date,
    parse_datetime,
    parse_non_negative_int,
    parse_positive_int,
    validate_breach_name,
    validate_ranges,
)
from app.core.pagination import normalize_page_size, total_pages
from app.domain.filters import BreachFilters
from app.infrastructure.persistence.repositories import BreachRepository
from app.schemas.breach import BreachResponse, PaginatedBreachesResponse

router = APIRouter(prefix="/breaches", tags=["breaches"])


@router.get("", response_model=PaginatedBreachesResponse)
def list_breaches(
    domain: str | None = None,
    name: str | None = None,
    breach_date_from: str | None = None,
    breach_date_to: str | None = None,
    added_date_from: str | None = None,
    added_date_to: str | None = None,
    data_class: str | None = None,
    min_pwn_count: str | None = None,
    max_pwn_count: str | None = None,
    is_verified: str | None = None,
    is_sensitive: str | None = None,
    is_spam_list: str | None = None,
    page: str = Query("1"),
    page_size: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaginatedBreachesResponse:
    parsed_page = parse_positive_int(page, field="page")
    raw_page_size = page_size or str(settings.page_size_default)
    parsed_page_size = parse_positive_int(raw_page_size, field="page_size")
    parsed_page_size = normalize_page_size(parsed_page_size, settings.page_size_max)

    if name is not None:
        validate_breach_name(name)

    parsed_breach_date_from = parse_date(breach_date_from, field="breach_date_from")
    parsed_breach_date_to = parse_date(breach_date_to, field="breach_date_to")
    parsed_added_date_from = parse_datetime(added_date_from, field="added_date_from")
    parsed_added_date_to = parse_datetime(added_date_to, field="added_date_to")
    parsed_min_pwn_count = parse_non_negative_int(min_pwn_count, field="min_pwn_count")
    parsed_max_pwn_count = parse_non_negative_int(max_pwn_count, field="max_pwn_count")
    parsed_is_verified = parse_bool(is_verified, field="is_verified")
    parsed_is_sensitive = parse_bool(is_sensitive, field="is_sensitive")
    parsed_is_spam_list = parse_bool(is_spam_list, field="is_spam_list")

    validate_ranges(
        breach_date_from=parsed_breach_date_from,
        breach_date_to=parsed_breach_date_to,
        added_date_from=parsed_added_date_from,
        added_date_to=parsed_added_date_to,
        min_pwn_count=parsed_min_pwn_count,
        max_pwn_count=parsed_max_pwn_count,
    )

    filters = BreachFilters(
        domain=domain,
        name=name,
        breach_date_from=parsed_breach_date_from,
        breach_date_to=parsed_breach_date_to,
        added_date_from=parsed_added_date_from,
        added_date_to=parsed_added_date_to,
        data_class=data_class,
        min_pwn_count=parsed_min_pwn_count,
        max_pwn_count=parsed_max_pwn_count,
        is_verified=parsed_is_verified,
        is_sensitive=parsed_is_sensitive,
        is_spam_list=parsed_is_spam_list,
    )
    service = BreachQueryService(BreachRepository(db))
    breaches, total = service.list_breaches(filters, page=parsed_page, page_size=parsed_page_size)
    return PaginatedBreachesResponse(
        page=parsed_page,
        page_size=parsed_page_size,
        total=total,
        total_pages=total_pages(total, parsed_page_size),
        items=[BreachResponse.model_validate(item) for item in breaches],
    )


@router.get("/{name}", response_model=BreachResponse)
def get_breach(name: str, db: Session = Depends(get_db)) -> BreachResponse:
    validate_breach_name(name)
    service = BreachQueryService(BreachRepository(db))
    return BreachResponse.model_validate(service.get_by_name(name))
