import re
from datetime import date, datetime

from app.application.exceptions import ValidationError

_NAME_RE = re.compile(r"^[A-Za-z0-9.\-]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_breach_name(name: str, *, field: str = "name") -> str:
    if not name or _NAME_RE.fullmatch(name) is None:
        raise ValidationError(
            f"{field} must be a non-empty slug containing only letters, digits, '.' and '-'.",
            field=field,
        )
    return name


def parse_date(value: str | None, *, field: str) -> date | None:
    if value is None:
        return None
    if _DATE_RE.fullmatch(value) is None:
        raise ValidationError(f"{field} must be a valid date in YYYY-MM-DD format.", field=field)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be a valid date in YYYY-MM-DD format.", field=field
        ) from exc


def parse_datetime(value: str | None, *, field: str) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"{field} must be a valid ISO 8601 datetime.", field=field) from exc


def parse_non_negative_int(value: str | None, *, field: str) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be an integer greater than or equal to zero.", field=field
        ) from exc
    if str(parsed) != value.strip() and not (
        value.strip().startswith("+") and str(parsed) == value.strip()[1:]
    ):
        raise ValidationError(
            f"{field} must be an integer greater than or equal to zero.", field=field
        )
    if parsed < 0:
        raise ValidationError(f"{field} must be greater than or equal to zero.", field=field)
    return parsed


def parse_positive_int(value: str, *, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError(f"{field} must be a positive integer.", field=field) from exc
    if str(parsed) != value.strip() and not (
        value.strip().startswith("+") and str(parsed) == value.strip()[1:]
    ):
        raise ValidationError(f"{field} must be a positive integer.", field=field)
    if parsed < 1:
        raise ValidationError(f"{field} must be greater than or equal to 1.", field=field)
    return parsed


def parse_bool(value: str | None, *, field: str) -> bool | None:
    if value is None:
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValidationError(f"{field} must be either true or false.", field=field)


def validate_ranges(
    *,
    breach_date_from: date | None,
    breach_date_to: date | None,
    added_date_from: datetime | None,
    added_date_to: datetime | None,
    min_pwn_count: int | None,
    max_pwn_count: int | None,
) -> None:
    if breach_date_from and breach_date_to and breach_date_from > breach_date_to:
        raise ValidationError(
            "breach_date_from cannot be after breach_date_to.", field="breach_date_from"
        )
    if added_date_from and added_date_to and added_date_from > added_date_to:
        raise ValidationError(
            "added_date_from cannot be after added_date_to.", field="added_date_from"
        )
    if min_pwn_count is not None and max_pwn_count is not None and min_pwn_count > max_pwn_count:
        raise ValidationError(
            "min_pwn_count cannot be greater than max_pwn_count.", field="min_pwn_count"
        )
