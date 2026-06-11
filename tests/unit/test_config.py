import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_reject_empty_hibp_user_agent() -> None:
    with pytest.raises(ValidationError):
        Settings(HIBP_USER_AGENT="")


def test_settings_reject_non_positive_timeout() -> None:
    with pytest.raises(ValidationError):
        Settings(HIBP_TIMEOUT_SECONDS=0)


def test_settings_reject_default_page_size_above_maximum() -> None:
    with pytest.raises(ValidationError, match="PAGE_SIZE_DEFAULT"):
        Settings(PAGE_SIZE_DEFAULT=101, PAGE_SIZE_MAX=100)
