import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.persistence.repositories import BreachRepository
from tests.factories import hibp_breach


@respx.mock
def test_sync_success_persists_breaches(client: TestClient, db_session: Session) -> None:
    route = respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(
            200, json=[hibp_breach(name="Adobe"), hibp_breach(name="Dropbox")]
        )
    )

    response = client.post("/sync")

    assert response.status_code == 200
    assert route.called
    assert route.calls[0].request.headers["User-Agent"] == "BreachRadar-Neuroscan-Challenge/1.0"
    body = response.json()
    assert body["source"] == "remote"
    assert body["inserted"] == 2
    assert body["updated"] == 0
    assert body["local_total"] == 2
    assert BreachRepository(db_session).count() == 2


@respx.mock
def test_sync_twice_is_idempotent(client: TestClient, db_session: Session) -> None:
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(200, json=[hibp_breach(name="Adobe", pwn_count=1)])
    )
    first = client.post("/sync")
    assert first.status_code == 200
    assert first.json()["inserted"] == 1

    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(200, json=[hibp_breach(name="Adobe", pwn_count=2)])
    )
    second = client.post("/sync")

    assert second.status_code == 200
    assert second.json()["inserted"] == 0
    assert second.json()["updated"] == 1
    assert BreachRepository(db_session).count() == 1
    detail = client.get("/breaches/Adobe").json()
    assert detail["pwn_count"] == 2


@respx.mock
def test_sync_timeout_uses_cache_fallback(client: TestClient, seed) -> None:
    seed(hibp_breach(name="Cached"))
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        side_effect=httpx.TimeoutException("timeout")
    )

    response = client.post("/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "cache_fallback"
    assert body["local_total"] == 1
    assert "timed out" in body["errors"][0]
    assert client.get("/breaches/Cached").status_code == 200


@respx.mock
def test_sync_http_500_uses_cache_fallback(client: TestClient, seed) -> None:
    seed(hibp_breach(name="Cached"))
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(500, text="boom")
    )

    response = client.post("/sync")

    assert response.status_code == 200
    assert response.json()["source"] == "cache_fallback"
    assert client.get("/breaches").json()["total"] == 1


@respx.mock
def test_sync_http_403_uses_cache_fallback(client: TestClient, seed) -> None:
    seed(hibp_breach(name="Cached"))
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(403, text="missing user agent")
    )

    response = client.post("/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "cache_fallback"
    assert "HTTP 403" in body["errors"][0]
    assert client.get("/breaches/Cached").status_code == 200


@respx.mock
def test_sync_malformed_json_is_controlled(client: TestClient, seed) -> None:
    seed(hibp_breach(name="Cached"))
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(
            200, content=b"{not-json", headers={"content-type": "application/json"}
        )
    )

    response = client.post("/sync")

    assert response.status_code == 200
    assert response.json()["source"] == "cache_fallback"
    assert "malformed JSON" in response.json()["errors"][0]


@respx.mock
def test_sync_handles_missing_relevant_fields(client: TestClient) -> None:
    incomplete = hibp_breach(name="Partial")
    incomplete.pop("DataClasses")
    incomplete.pop("Domain")
    incomplete.pop("BreachDate")

    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(200, json=[incomplete])
    )

    response = client.post("/sync")
    detail = client.get("/breaches/Partial")

    assert response.status_code == 200
    assert response.json()["inserted"] == 1
    assert detail.status_code == 200
    assert detail.json()["domain"] is None
    assert detail.json()["breach_date"] is None
    assert detail.json()["data_classes"] == []


@respx.mock
def test_sync_ignores_bad_record_and_persists_valid_record(client: TestClient) -> None:
    bad = hibp_breach(name="Bad Name With Space")
    good = hibp_breach(name="Good")

    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(200, json=[bad, good])
    )

    response = client.post("/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 1
    assert body["ignored"] == 1
    assert client.get("/breaches/Good").status_code == 200
