from legacy.breach_matcher import (
    data_class_matches,
    domain_matches,
    filter_breaches,
    is_valid_breach_name,
    paginate,
    within_breach_date,
)


def test_is_valid_breach_name_accepts_only_expected_slug_chars() -> None:
    assert is_valid_breach_name("Adobe-2024.v2") is True
    assert is_valid_breach_name("") is False
    assert is_valid_breach_name("Bad Name") is False
    assert is_valid_breach_name("bad;drop") is False


def test_domain_matches_is_case_insensitive_for_domain_and_query() -> None:
    assert domain_matches({"Domain": "dropbox.com"}, "Dropbox") is True
    assert domain_matches({"Domain": "DROPBOX.COM"}, "drop") is True
    assert domain_matches({"Domain": ""}, "drop") is False
    assert domain_matches({}, "drop") is False


def test_within_breach_date_includes_date_to() -> None:
    breach = {"BreachDate": "2019-12-31"}

    assert within_breach_date(breach, "2019-01-01", "2019-12-31") is True
    assert within_breach_date(breach, "2020-01-01", None) is False
    assert within_breach_date(breach, None, "2019-01-01") is False


def test_paginate_returns_exactly_page_size_and_does_not_drop_items() -> None:
    items = list(range(45))

    assert paginate(items, page=1, page_size=20) == list(range(20))
    assert paginate(items, page=2, page_size=20) == list(range(20, 40))
    assert paginate(items, page=3, page_size=20) == list(range(40, 45))


def test_data_class_matches_is_case_insensitive() -> None:
    breach = {"DataClasses": ["Email addresses", "Passwords"]}

    assert data_class_matches(breach, " passwords ") is True
    assert data_class_matches(breach, "Phone numbers") is False


def test_filter_breaches_applies_all_filters_with_and_semantics() -> None:
    breaches = [
        {
            "Name": "Adobe",
            "Domain": "adobe.com",
            "BreachDate": "2013-10-04",
            "PwnCount": 100,
            "DataClasses": ["Passwords"],
        },
        {
            "Name": "Other",
            "Domain": "other.com",
            "BreachDate": "2013-10-04",
            "PwnCount": 100,
            "DataClasses": ["Passwords"],
        },
        {
            "Name": "SmallAdobe",
            "Domain": "adobe.example",
            "BreachDate": "2013-10-04",
            "PwnCount": 1,
            "DataClasses": ["Passwords"],
        },
    ]

    result = filter_breaches(
        breaches,
        domain="adobe",
        data_class="passwords",
        breach_date_from="2013-01-01",
        breach_date_to="2013-12-31",
        min_pwn_count=10,
        max_pwn_count=100,
    )

    assert [item["Name"] for item in result] == ["Adobe"]
