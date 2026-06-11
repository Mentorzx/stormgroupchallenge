from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class BreachResponse(BaseModel):
    name: str
    title: str | None
    domain: str | None
    breach_date: date | None
    added_date: datetime | None
    modified_date: datetime | None
    pwn_count: int
    description: str | None
    description_plain_text: str | None
    logo_path: str | None
    data_classes: list[str]
    is_verified: bool
    is_fabricated: bool
    is_sensitive: bool
    is_retired: bool
    is_spam_list: bool
    is_malware: bool

    model_config = ConfigDict(from_attributes=True)


class PaginatedBreachesResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[BreachResponse]


class SyncResponse(BaseModel):
    source: str
    status: str
    provider: str
    total_received: int
    inserted: int
    updated: int
    ignored: int
    local_total: int
    errors: list[str]


class ErrorResponse(BaseModel):
    detail: str
