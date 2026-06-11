import os

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _base_url() -> str:
    value = os.getenv("E2E_BASE_URL")
    if not value:
        pytest.skip("E2E_BASE_URL is required for HTTP end-to-end tests.")
    return value.rstrip("/")


def test_e2e_health_and_openapi_over_http() -> None:
    base_url = _base_url()

    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        health = client.get("/health")
        openapi = client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert openapi.status_code == 200
    assert "/breaches" in openapi.json()["paths"]


def test_e2e_breaches_empty_catalog_over_http() -> None:
    base_url = _base_url()

    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        response = client.get("/breaches", params={"page": "1", "page_size": "5"})

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["items"] == []
