import pytest

from app.infrastructure.persistence import session as session_module


class FakeSession:
    def __init__(self) -> None:
        self.closed = False
        self.rolled_back = False

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def test_get_db_rolls_back_and_closes_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(session_module, "get_session_factory", lambda: lambda: fake_session)

    db = session_module.get_db()
    assert next(db) is fake_session

    with pytest.raises(RuntimeError, match="boom"):
        db.throw(RuntimeError("boom"))

    assert fake_session.rolled_back is True
    assert fake_session.closed is True
