from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_checks_database(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_openapi_is_exposed(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "Breach Radar"

    paths = body["paths"]
    assert set(paths) >= {"/health", "/ready", "/sync", "/breaches", "/breaches/{name}"}
    assert set(paths["/sync"]) == {"post"}
    assert set(paths["/breaches"]) == {"get"}
    assert set(paths["/breaches/{name}"]) == {"get"}

    breach_params = {param["name"] for param in paths["/breaches"]["get"]["parameters"]}
    assert {
        "domain",
        "name",
        "breach_date_from",
        "breach_date_to",
        "added_date_from",
        "added_date_to",
        "data_class",
        "min_pwn_count",
        "max_pwn_count",
        "is_verified",
        "is_sensitive",
        "is_spam_list",
        "page",
        "page_size",
    } <= breach_params

    responses = paths["/breaches"]["get"]["responses"]
    assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "PaginatedBreachesResponse"
    )


def test_swagger_docs_are_exposed(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text
