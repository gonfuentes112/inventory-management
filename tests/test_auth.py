from fastapi.testclient import TestClient


def test_login_success(client: TestClient, test_data):
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_data):
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_create_product_requires_authentication(client: TestClient):
    response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "owner_id": 1,
            "category_id": 1,
        },
    )

    assert response.status_code == 401


def test_create_product_with_authentication(
    authenticated_client: TestClient,
    test_data,
):
    response = authenticated_client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "quantity": 10,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["owner_id"] == test_data["user"].id


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/users/login",
        json={
            "username": "doesnotexist",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_missing_password(client: TestClient):
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422


def test_login_missing_username(client: TestClient):
    response = client.post(
        "/users/login",
        json={
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422


def test_invalid_token_cannot_access_protected_endpoint(
    client: TestClient,
):
    response = client.get(
        "/users",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
