import pytest

from app.infrastructure.hibp.mapper import HIBPMappingError, map_hibp_breach
from tests.factories import hibp_breach


def test_mapper_rejects_non_object_payload() -> None:
    with pytest.raises(HIBPMappingError, match="object"):
        map_hibp_breach(["not", "a", "dict"])  # type: ignore[arg-type]


def test_mapper_rejects_missing_name() -> None:
    payload = hibp_breach()
    payload.pop("Name")

    with pytest.raises(HIBPMappingError, match="Name"):
        map_hibp_breach(payload)


def test_mapper_normalizes_non_list_data_classes_to_empty_list() -> None:
    row = map_hibp_breach(hibp_breach(DataClasses="Passwords"))

    assert row["data_classes"] == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("BreachDate", 123, "YYYY-MM-DD"),
        ("BreachDate", "not-a-date", "YYYY-MM-DD"),
        ("BreachDate", "20200101", "YYYY-MM-DD"),
        ("BreachDate", "2020-W01-1", "YYYY-MM-DD"),
        ("AddedDate", 123, "ISO 8601"),
        ("AddedDate", "not-a-datetime", "ISO 8601"),
        ("PwnCount", True, "integer"),
        ("PwnCount", "many", "integer"),
        ("PwnCount", -1, "greater than or equal to zero"),
    ],
)
def test_mapper_rejects_malformed_fields(field: str, value, message: str) -> None:
    with pytest.raises(HIBPMappingError, match=message):
        map_hibp_breach(hibp_breach(**{field: value}))
