import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserResponse


def test_user_create():
    user = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="not-an-email",
            password="testpassword123",
        )


def test_user_create_empty_username():
    with pytest.raises(ValidationError):
        UserCreate(
            username="",
            email="test@example.com",
            password="testpassword123",
        )


def test_user_response_from_orm():
    user = UserResponse.model_validate(
        {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
        }
    )

    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"
