import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db, get_settings
from app.core.config import Settings
from app.infrastructure.hibp.mapper import map_hibp_breach
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories import BreachRepository
from app.main import create_app


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        APP_ENV="test",
        DATABASE_URL="sqlite+pysqlite://",
        HIBP_BREACHES_URL="https://haveibeenpwned.com/api/v3/breaches",
        HIBP_USER_AGENT="BreachRadar-Neuroscan-Challenge/1.0",
        HIBP_TIMEOUT_SECONDS=1,
        PAGE_SIZE_DEFAULT=20,
        PAGE_SIZE_MAX=100,
        LOG_LEVEL="WARNING",
    )


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url:
        engine = create_engine(database_url, pool_pre_ping=True)
    else:
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session, settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_db() -> Generator[Session, None, None]:
        yield db_session

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def seed(db_session: Session):
    def _seed(*records: dict) -> None:
        repo = BreachRepository(db_session)
        rows = [map_hibp_breach(record) for record in records]
        repo.upsert_many(rows)
        db_session.commit()

    return _seed
