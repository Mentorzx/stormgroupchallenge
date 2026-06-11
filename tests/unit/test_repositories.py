from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.hibp.mapper import map_hibp_breach
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories import BreachRepository
from tests.factories import hibp_breach


def test_sqlite_upsert_branch_inserts_and_updates() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    repo = BreachRepository(session)

    assert repo.existing_names([]) == set()

    repo.upsert_many([map_hibp_breach(hibp_breach(name="Adobe", pwn_count=1))])
    session.commit()
    repo.upsert_many([map_hibp_breach(hibp_breach(name="Adobe", pwn_count=2))])
    session.commit()

    assert repo.count() == 1
    assert repo.get("Adobe").pwn_count == 2

    session.close()
    engine.dispose()
