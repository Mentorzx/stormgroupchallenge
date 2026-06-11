import logging
from typing import Any

import httpx

from app.application.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class HIBPClient:
    """Small HTTP client for the public HIBP breaches feed."""

    def __init__(self, *, url: str, user_agent: str, timeout_seconds: float) -> None:
        self.url = url
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    def fetch_breaches(self) -> list[dict[str, Any]]:
        """Fetch the raw breach catalog from HIBP.

        Returns:
            A list of raw breach dictionaries.

        Raises:
            ExternalServiceError: If the request fails, returns an HTTP error,
                returns malformed JSON, or does not return a JSON array.
        """
        headers = {"User-Agent": self.user_agent}
        try:
            with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
                response = client.get(self.url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("HIBP timeout", extra={"event_error": "timeout"})
            raise ExternalServiceError("HIBP request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("HIBP HTTP error", extra={"event_status_code": status})
            raise ExternalServiceError(f"HIBP returned HTTP {status}.") from exc
        except httpx.HTTPError as exc:
            logger.warning("HIBP HTTP client error", extra={"event_error": str(exc)})
            raise ExternalServiceError("HIBP request failed.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning("HIBP malformed JSON")
            raise ExternalServiceError("HIBP returned malformed JSON.") from exc

        if not isinstance(payload, list):
            raise ExternalServiceError("HIBP response must be a JSON array.")

        return payload
