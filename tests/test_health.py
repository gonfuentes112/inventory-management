from fastapi.testclient import TestClient

from app.db.database import engine
from app.main import app


def test_health_returns_ok_when_database_is_available() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_database_is_unavailable(
    monkeypatch,
) -> None:
    def raise_database_error(*args, **kwargs):
        raise Exception("Database connection failed")

    monkeypatch.setattr(
        engine,
        "connect",
        raise_database_error,
    )

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
