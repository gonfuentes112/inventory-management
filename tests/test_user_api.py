from fastapi.testclient import TestClient


def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
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


def test_get_users(client: TestClient):
    client.post(
        "/users",
        json={
            "username": "user1",
            "email": "user1@example.com",
        },
    )
    client.post(
        "/users",
        json={
            "username": "user2",
            "email": "user2@example.com",
        },
    )

    response = client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["username"] == "user1"
    assert data[1]["username"] == "user2"


def test_get_user(client: TestClient):
    create_response = client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
        },
    )

    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_user_not_found(client: TestClient):
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_create_user_duplicate_email(client: TestClient):
    client.post(
        "/users",
        json={
            "username": "user1",
            "email": "same@example.com",
        },
    )

    response = client.post(
        "/users",
        json={
            "username": "user2",
            "email": "same@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"
