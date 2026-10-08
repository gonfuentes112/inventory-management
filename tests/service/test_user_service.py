import pytest

from sqlalchemy.orm import Session

from app.schemas.user import UserCreate
from app.services.user import UserService


def test_create_user(db_session: Session):
    service = UserService(db_session)

    data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )
    user = service.create_user(data)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_get_user(db_session: Session):
    service = UserService(db_session)

    data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )
    user = service.create_user(data)
    result = service.get_user(user.id)

    assert result is not None
    assert result.id == user.id
    assert result.username == "testuser"
    assert result.email == "test@example.com"


def test_get_user_not_found(db_session: Session):
    service = UserService(db_session)

    result = service.get_user(999)

    assert result is None


def test_get_users(db_session: Session):
    service = UserService(db_session)
    service.create_user(
        UserCreate(
            username="user1",
            email="user1@example.com",
            password="testpassword123",
        )
    )
    service.create_user(
        UserCreate(
            username="user2",
            email="user2@example.com",
            password="testpassword123",
        )
    )

    users = service.get_users()

    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"


def test_create_user_duplicate_username(db_session: Session):
    service = UserService(db_session)

    service.create_user(
        UserCreate(
            username="testuser",
            email="first@example.com",
            password="testpassword123",
        )
    )

    with pytest.raises(ValueError, match="Username already exists"):
        service.create_user(
            UserCreate(
                username="testuser",
                email="second@example.com",
                password="testpassword123",
            )
        )


def test_create_user_duplicate_email(db_session: Session):
    service = UserService(db_session)

    service.create_user(
        UserCreate(
            username="firstuser",
            email="test@example.com",
            password="testpassword123",
        )
    )

    with pytest.raises(ValueError, match="Email already exists"):
        service.create_user(
            UserCreate(
                username="seconduser",
                email="test@example.com",
                password="testpassword123",
            )
        )
