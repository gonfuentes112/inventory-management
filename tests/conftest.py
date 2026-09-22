import pytest
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.category import Category
from app.models.product import Product  # type: ignore
from app.models.user import User

from collections.abc import Generator

from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app

from sqlalchemy.pool import StaticPool

from app.core.security import hash_password


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def test_data(db_session: Session) -> dict[str, User | Category]:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    return {
        "user": user,
        "category": category,
    }
