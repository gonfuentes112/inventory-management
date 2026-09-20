from fastapi.testclient import TestClient


def test_create_category(client: TestClient):
    response = client.post(
        "/categories",
        json={"name": "Electronics"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Electronics"


def test_get_categories(client: TestClient):
    client.post(
        "/categories",
        json={"name": "Electronics"},
    )
    client.post(
        "/categories",
        json={"name": "Books"},
    )
    response = client.get("/categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Electronics"
    assert data[1]["name"] == "Books"


def test_get_category(client: TestClient):
    create_response = client.post(
        "/categories",
        json={"name": "Electronics"},
    )

    category_id = create_response.json()["id"]

    response = client.get(f"/categories/{category_id}")

    assert response.status_code == 200
    assert response.json()["id"] == category_id
    assert response.json()["name"] == "Electronics"


def test_get_category_not_found(client: TestClient):
    response = client.get("/categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_delete_category(client: TestClient):
    create_response = client.post(
        "/categories",
        json={"name": "Electronics"},
    )

    category_id = create_response.json()["id"]

    response = client.delete(f"/categories/{category_id}")

    assert response.status_code == 204

    response = client.get(f"/categories/{category_id}")

    assert response.status_code == 404


def test_delete_category_not_found(client: TestClient):
    response = client.delete("/categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_create_category_validation(client: TestClient):
    response = client.post(
        "/categories",
        json={"name": ""},
    )

    assert response.status_code == 422
