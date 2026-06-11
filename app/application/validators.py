import re
from datetime import UTC, date, datetime

from app.application.exceptions import ValidationError

_NAME_RE = re.compile(r"^[A-Za-z0-9.\-]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NON_NEGATIVE_INT_RE = re.compile(r"^\d+$")
_POSITIVE_INT_RE = re.compile(r"^[1-9]\d*$")


def validate_breach_name(name: str, *, field: str = "name") -> str:
    """Validate the HIBP breach slug used by routes and persistence.

    Args:
        name: Candidate breach name.
        field: Field name used in the validation error.

    Returns:
        The original name when it matches the accepted slug format.

    Raises:
        ValidationError: If the name is blank or contains unsupported characters.
    """
    if not name or _NAME_RE.fullmatch(name) is None:
        raise ValidationError(
            f"{field} must be a non-empty slug containing only letters, digits, '.' and '-'.",
            field=field,
        )
    return name


def parse_date(value: str | None, *, field: str) -> date | None:
    """Parse a strict `YYYY-MM-DD` query parameter.

    Args:
        value: Raw query parameter value.
        field: Field name used in the validation error.

    Returns:
        Parsed date, or `None` when the parameter was omitted.

    Raises:
        ValidationError: If the value is not a calendar date in `YYYY-MM-DD` form.
    """
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
    """Parse an ISO 8601 datetime and normalize naive values to UTC.

    Args:
        value: Raw query parameter value.
        field: Field name used in the validation error.

    Returns:
        Timezone-aware datetime, or `None` when the parameter was omitted.

    Raises:
        ValidationError: If the value cannot be parsed as ISO 8601.
    """
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"{field} must be a valid ISO 8601 datetime.", field=field) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def parse_non_negative_int(value: str | None, *, field: str) -> int | None:
    if value is None:
        return None
    if _NON_NEGATIVE_INT_RE.fullmatch(value) is None:
        raise ValidationError(
            f"{field} must be an integer greater than or equal to zero.", field=field
        )
    return int(value)


def parse_positive_int(value: str, *, field: str) -> int:
    if _POSITIVE_INT_RE.fullmatch(value) is None:
        raise ValidationError(f"{field} must be a positive integer.", field=field)
    return int(value)


def parse_non_blank_text(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    parsed = value.strip()
    if not parsed:
        raise ValidationError(f"{field} must not be empty.", field=field)
    return parsed


def parse_bool(value: str | None, *, field: str) -> bool | None:
    """Parse a boolean query parameter without accepting loose aliases.

    Args:
        value: Raw query parameter value.
        field: Field name used in the validation error.

    Returns:
        `True`, `False`, or `None` when the parameter was omitted.

    Raises:
        ValidationError: If the value is not exactly `true` or `false`.
    """
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
    """Reject inverted filter ranges before they reach the repository.

    Raises:
        ValidationError: If a lower bound is greater than its matching upper bound.
    """
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
