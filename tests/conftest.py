import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.category import Category  # type: ignore
from app.models.product import Product  # type: ignore
from app.models.user import User  # type: ignore


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()
