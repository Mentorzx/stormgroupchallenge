import httpx
import pytest
import respx

from app.application.exceptions import ExternalServiceError
from app.infrastructure.hibp.client import HIBPClient


def make_client() -> HIBPClient:
    return HIBPClient(
        url="https://haveibeenpwned.com/api/v3/breaches",
        user_agent="BreachRadar-Neuroscan-Challenge/1.0",
        timeout_seconds=1,
    )


@respx.mock
def test_hibp_client_rejects_non_array_json() -> None:
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        return_value=httpx.Response(200, json={"Name": "Adobe"})
    )

    with pytest.raises(ExternalServiceError, match="JSON array"):
        make_client().fetch_breaches()


@respx.mock
def test_hibp_client_wraps_http_client_errors() -> None:
    respx.get("https://haveibeenpwned.com/api/v3/breaches").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    with pytest.raises(ExternalServiceError, match="request failed"):
        make_client().fetch_breaches()
