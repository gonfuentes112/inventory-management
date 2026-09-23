from fastapi.testclient import TestClient

from app.core.security import hash_password

from app.models.category import Category
from app.models.user import User


def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": hash_password("testpassword123"),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


def test_create_user_invalid_data(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
        },
    )

    assert response.status_code == 422


def test_create_duplicate_user(client: TestClient):
    user_data = {
        "username": "duplicate",
        "email": "duplicate@example.com",
        "password": hash_password("testpassword123"),
    }

    first_response = client.post(
        "/users",
        json=user_data,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/users",
        json=user_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Username already exists"


def test_get_users(authenticated_client: TestClient):
    authenticated_client.post(
        "/users",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": hash_password("testpassword123"),
        },
    )
    authenticated_client.post(
        "/users",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": hash_password("testpassword123"),
        },
    )

    response = authenticated_client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3  # counts authenticated testuser as well
    assert data[0]["username"] == "testuser"
    assert data[1]["username"] == "user1"
    assert data[2]["username"] == "user2"


def test_get_user(authenticated_client: TestClient):
    create_response = authenticated_client.post(
        "/users",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": hash_password("newpassword123"),
        },
    )

    user_id = create_response.json()["id"]

    response = authenticated_client.get(f"/users/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"


def test_get_user_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_create_user_duplicate_email(client: TestClient):
    client.post(
        "/users",
        json={
            "username": "user1",
            "email": "same@example.com",
            "password": hash_password("testpassword123"),
        },
    )

    response = client.post(
        "/users",
        json={
            "username": "user2",
            "email": "same@example.com",
            "password": hash_password("testpassword123"),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


def test_unauthenticated_cannot_get_users(
    client: TestClient,
):
    response = client.get("/users")

    assert response.status_code == 401


def test_unauthenticated_cannot_get_user(
    client: TestClient,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 401
