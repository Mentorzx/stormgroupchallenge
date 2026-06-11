import re
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import Any

from app.application.validators import validate_breach_name


class HIBPMappingError(ValueError):
    """Raised when an HIBP record cannot be mapped safely."""


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join("".join(self.parts).split())


def map_hibp_breach(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert one HIBP breach record into the persistence shape.

    Args:
        payload: Raw breach object returned by HIBP.

    Returns:
        Dictionary ready to be passed to `BreachRepository.upsert_many`.

    Raises:
        HIBPMappingError: If required fields are absent or typed unsafely.
        ValidationError: If the HIBP `Name` does not match the local slug rules.
    """
    if not isinstance(payload, dict):
        raise HIBPMappingError("record must be an object")

    raw_name = payload.get("Name")
    if not isinstance(raw_name, str):
        raise HIBPMappingError("Name is required and must be a string")
    name = validate_breach_name(raw_name)

    data_classes = payload.get("DataClasses") or []
    if not isinstance(data_classes, list):
        data_classes = []
    normalized_data_classes = [item for item in data_classes if isinstance(item, str)]
    searchable_data_classes = [item.strip().lower() for item in normalized_data_classes]
    description = _optional_str(payload.get("Description"), "Description")

    return {
        "name": name,
        "title": _optional_str(payload.get("Title"), "Title") or name,
        "domain": _optional_str(payload.get("Domain"), "Domain"),
        "breach_date": _optional_date(payload.get("BreachDate"), "BreachDate"),
        "added_date": _optional_datetime(payload.get("AddedDate"), "AddedDate"),
        "modified_date": _optional_datetime(payload.get("ModifiedDate"), "ModifiedDate"),
        "pwn_count": _non_negative_int(payload.get("PwnCount"), "PwnCount"),
        "description": description,
        "description_plain_text": _plain_text(description),
        "logo_path": _optional_str(payload.get("LogoPath"), "LogoPath"),
        "data_classes": normalized_data_classes,
        "data_classes_normalized": searchable_data_classes,
        "is_verified": _bool(payload.get("IsVerified"), "IsVerified"),
        "is_fabricated": _bool(payload.get("IsFabricated"), "IsFabricated"),
        "is_sensitive": _bool(payload.get("IsSensitive"), "IsSensitive"),
        "is_retired": _bool(payload.get("IsRetired"), "IsRetired"),
        "is_spam_list": _bool(payload.get("IsSpamList"), "IsSpamList"),
        "is_malware": _bool(payload.get("IsMalware"), "IsMalware"),
        "raw_payload": payload,
    }


def _optional_str(value: Any, field: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise HIBPMappingError(f"{field} must be a string")
    return value


def _plain_text(value: str | None) -> str | None:
    if value is None:
        return None
    parser = _PlainTextParser()
    parser.feed(value)
    parser.close()
    text = parser.text()
    return text or None


def _optional_date(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise HIBPMappingError(f"{field} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HIBPMappingError(f"{field} must be YYYY-MM-DD") from exc


def _optional_datetime(value: Any, field: str) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise HIBPMappingError(f"{field} must be ISO 8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HIBPMappingError(f"{field} must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _non_negative_int(value: Any, field: str) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, bool):
        raise HIBPMappingError(f"{field} must be an integer")
    if not isinstance(value, int):
        raise HIBPMappingError(f"{field} must be an integer")
    if value < 0:
        raise HIBPMappingError(f"{field} must be greater than or equal to zero")
    return value


def _bool(value: Any, field: str) -> bool:
    if value is None:
        return False
    if not isinstance(value, bool):
        raise HIBPMappingError(f"{field} must be a boolean")
    return value
