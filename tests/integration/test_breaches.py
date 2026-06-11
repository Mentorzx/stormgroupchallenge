from fastapi.testclient import TestClient

from tests.factories import hibp_breach


def seed_catalog(seed) -> None:
    seed(
        hibp_breach(
            name="Adobe",
            domain="adobe.com",
            breach_date="2013-10-04",
            added_date="2013-12-04T00:00:00Z",
            pwn_count=152445165,
            data_classes=["Email addresses", "Password hints", "Passwords"],
            is_verified=True,
            is_sensitive=False,
            is_spam_list=False,
        ),
        hibp_breach(
            name="Dropbox",
            domain="dropbox.com",
            breach_date="2012-07-01",
            added_date="2016-08-31T00:00:00Z",
            pwn_count=68648009,
            data_classes=["Email addresses", "Passwords"],
            is_verified=True,
            is_sensitive=False,
            is_spam_list=False,
        ),
        hibp_breach(
            name="SensitiveBreach",
            domain="secret.example",
            breach_date="2020-01-15",
            added_date="2020-02-01T12:00:00Z",
            pwn_count=50,
            data_classes=["Email addresses", "Government IDs"],
            is_verified=False,
            is_sensitive=True,
            is_spam_list=False,
        ),
        hibp_breach(
            name="SpamList",
            domain=None,
            breach_date="2021-03-20",
            added_date="2021-04-01T12:00:00Z",
            pwn_count=999,
            data_classes=["Email addresses"],
            is_verified=True,
            is_sensitive=False,
            is_spam_list=True,
        ),
    )


def names(body: dict) -> list[str]:
    return [item["name"] for item in body["items"]]


def test_list_breaches_default_pagination(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches")

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 4
    assert body["total_pages"] == 1
    assert set(names(body)) == {"Adobe", "Dropbox", "SensitiveBreach", "SpamList"}


def test_filter_domain_is_partial_case_insensitive_and_excludes_null(
    client: TestClient, seed
) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?domain=DROP")

    assert response.status_code == 200
    assert names(response.json()) == ["Dropbox"]


def test_filter_name_exact(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?name=Adobe")

    assert response.status_code == 200
    assert names(response.json()) == ["Adobe"]


def test_filter_breach_date_inclusive_window(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?breach_date_from=2013-10-04&breach_date_to=2013-10-04")

    assert response.status_code == 200
    assert names(response.json()) == ["Adobe"]


def test_filter_added_date_inclusive_window(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get(
        "/breaches?added_date_from=2016-08-31T00:00:00Z&added_date_to=2016-08-31T00:00:00Z"
    )

    assert response.status_code == 200
    assert names(response.json()) == ["Dropbox"]


def test_filter_data_class_case_insensitive(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?data_class=government ids")

    assert response.status_code == 200
    assert names(response.json()) == ["SensitiveBreach"]


def test_filter_pwn_count_range(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?min_pwn_count=900&max_pwn_count=1000")

    assert response.status_code == 200
    assert names(response.json()) == ["SpamList"]


def test_filter_is_verified(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?is_verified=false")

    assert response.status_code == 200
    assert names(response.json()) == ["SensitiveBreach"]


def test_filter_is_sensitive(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?is_sensitive=true")

    assert response.status_code == 200
    assert names(response.json()) == ["SensitiveBreach"]


def test_filter_is_spam_list(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?is_spam_list=true")

    assert response.status_code == 200
    assert names(response.json()) == ["SpamList"]


def test_combined_filters_use_and_semantics(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get(
        "/breaches?domain=example&data_class=government ids&is_sensitive=true&max_pwn_count=100"
    )

    assert response.status_code == 200
    assert names(response.json()) == ["SensitiveBreach"]


def test_combined_filters_return_empty_when_any_condition_fails(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches?domain=example&is_spam_list=true")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_get_detail_by_name(client: TestClient, seed) -> None:
    seed_catalog(seed)

    response = client.get("/breaches/Adobe")

    assert response.status_code == 200
    assert response.json()["name"] == "Adobe"
    assert response.json()["domain"] == "adobe.com"


def test_get_detail_invalid_slug_returns_400(client: TestClient) -> None:
    response = client.get("/breaches/Invalid%20Name")

    assert response.status_code == 400
    assert "name must be" in response.json()["detail"]


def test_get_detail_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/breaches/Missing")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_invalid_name_filter_returns_400(client: TestClient) -> None:
    response = client.get("/breaches?name=bad;drop")

    assert response.status_code == 400
    assert "name must be" in response.json()["detail"]


def test_invalid_date_returns_400(client: TestClient) -> None:
    response = client.get("/breaches?breach_date_from=2020-99-99")

    assert response.status_code == 400
    assert "breach_date_from" in response.json()["detail"]


def test_breach_date_must_use_hyphenated_yyyy_mm_dd(client: TestClient) -> None:
    compact = client.get("/breaches?breach_date_from=20200101")
    week_date = client.get("/breaches?breach_date_to=2020-W01-1")

    assert compact.status_code == 400
    assert "YYYY-MM-DD" in compact.json()["detail"]
    assert week_date.status_code == 400
    assert "YYYY-MM-DD" in week_date.json()["detail"]


def test_invalid_added_date_returns_400(client: TestClient) -> None:
    response = client.get("/breaches?added_date_from=not-a-date")

    assert response.status_code == 400
    assert "added_date_from" in response.json()["detail"]


def test_invalid_pwn_count_returns_400(client: TestClient) -> None:
    response = client.get("/breaches?min_pwn_count=-1")

    assert response.status_code == 400
    assert "min_pwn_count" in response.json()["detail"]


def test_invalid_bool_returns_400(client: TestClient) -> None:
    response = client.get("/breaches?is_verified=yes")

    assert response.status_code == 400
    assert "is_verified" in response.json()["detail"]


def test_invalid_ranges_return_400(client: TestClient) -> None:
    response = client.get("/breaches?breach_date_from=2021-01-01&breach_date_to=2020-01-01")

    assert response.status_code == 400
    assert "breach_date_from" in response.json()["detail"]

    response = client.get(
        "/breaches?added_date_from=2021-01-01T00:00:00Z&added_date_to=2020-01-01T00:00:00Z"
    )
    assert response.status_code == 400
    assert "added_date_from" in response.json()["detail"]

    response = client.get("/breaches?min_pwn_count=10&max_pwn_count=1")
    assert response.status_code == 400
    assert "min_pwn_count" in response.json()["detail"]


def test_pagination_first_last_empty_and_capped_page_size(client: TestClient, seed) -> None:
    seed(*(hibp_breach(name=f"Breach-{index:02d}", pwn_count=index) for index in range(25)))

    first = client.get("/breaches?page=1&page_size=10")
    last = client.get("/breaches?page=3&page_size=10")
    empty = client.get("/breaches?page=4&page_size=10")
    capped = client.get("/breaches?page=1&page_size=10000")

    assert first.status_code == 200
    assert len(first.json()["items"]) == 10
    assert first.json()["total_pages"] == 3

    assert last.status_code == 200
    assert len(last.json()["items"]) == 5

    assert empty.status_code == 200
    assert empty.json()["items"] == []

    assert capped.status_code == 200
    assert capped.json()["page_size"] == 100
    assert len(capped.json()["items"]) == 25


def test_invalid_pagination_returns_400(client: TestClient) -> None:
    assert client.get("/breaches?page=0").status_code == 400
    assert client.get("/breaches?page_size=0").status_code == 400
    assert client.get("/breaches?page=abc").status_code == 400
