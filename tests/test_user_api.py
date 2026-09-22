from pytest import raises
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


def test_create_user_invalid_data(client: TestClient):
    response = client.post(
        "/users/",
        json={
            "username": "newuser",
        },
    )

    assert response.status_code == 422


def test_create_duplicate_user(client: TestClient):
    user_data = {
        "username": "duplicate",
        "email": "duplicate@example.com",
    }

    first_response = client.post(
        "/users/",
        json=user_data,
    )

    assert first_response.status_code == 200

    with raises(IntegrityError):
        client.post(
            "/users/",
            json=user_data,
        )
