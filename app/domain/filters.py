from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class BreachFilters:
    domain: str | None = None
    name: str | None = None
    breach_date_from: date | None = None
    breach_date_to: date | None = None
    added_date_from: datetime | None = None
    added_date_to: datetime | None = None
    data_class: str | None = None
    min_pwn_count: int | None = None
    max_pwn_count: int | None = None
    is_verified: bool | None = None
    is_sensitive: bool | None = None
    is_spam_list: bool | None = None
