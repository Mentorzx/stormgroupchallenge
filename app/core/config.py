from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/breach_radar",
        alias="DATABASE_URL",
    )
    hibp_breaches_url: str = Field(
        default="https://haveibeenpwned.com/api/v3/breaches",
        alias="HIBP_BREACHES_URL",
    )
    hibp_user_agent: str = Field(
        default="BreachRadar-Neuroscan-Challenge/1.0",
        alias="HIBP_USER_AGENT",
        min_length=1,
    )
    hibp_timeout_seconds: float = Field(default=10.0, alias="HIBP_TIMEOUT_SECONDS", gt=0)
    page_size_default: int = Field(default=20, alias="PAGE_SIZE_DEFAULT", ge=1)
    page_size_max: int = Field(default=100, alias="PAGE_SIZE_MAX", ge=1)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_page_size_bounds(self) -> "Settings":
        if self.page_size_default > self.page_size_max:
            raise ValueError("PAGE_SIZE_DEFAULT cannot be greater than PAGE_SIZE_MAX.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
