from fastapi.testclient import TestClient
from app.models.category import Category
from app.models.user import User


def test_create_product(client: TestClient, test_data: dict[str, User | Category]):
    response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["price"] == 1200.00


def test_get_product(client: TestClient, test_data: dict[str, User | Category]):
    create_response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_get_product_not_found(client: TestClient):
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product(client: TestClient, test_data: dict[str, User | Category]):
    create_response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        json={
            "name": "Gaming Laptop",
            "price": 1800.00,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Gaming Laptop"
    assert data["price"] == 1800.00


def test_delete_product(client: TestClient, test_data: dict[str, User | Category]):
    create_response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    product_id = create_response.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(f"/products/{product_id}")

    assert get_response.status_code == 404


def test_create_product_validation(
    client: TestClient, test_data: dict[str, User | Category]
):
    response = client.post(
        "/products",
        json={
            "name": "",
            "description": "Invalid product",
            "price": -100,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    assert response.status_code == 422
