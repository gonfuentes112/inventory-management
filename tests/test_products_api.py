from fastapi.testclient import TestClient
from app.models.category import Category
from app.models.user import User

from sqlalchemy.orm import Session

from app.models.product import Product


def test_create_product(
    authenticated_client: TestClient, test_data: dict[str, User | Category]
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
    assert data["price"] == 1200.00


def test_create_product_requires_authentication(client: TestClient):
    response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "quantity": 10,
            "owner_id": 1,
            "category_id": 1,
        },
    )

    assert response.status_code == 401


def test_get_product(
    authenticated_client: TestClient, test_data: dict[str, User | Category]
):
    create_response = authenticated_client.post(
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

    product_id = create_response.json()["id"]

    response = authenticated_client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_get_product_not_found(client: TestClient):
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_get_products(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    authenticated_client.post(
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

    authenticated_client.post(
        "/products",
        json={
            "name": "Keyboard",
            "description": "Mechanical keyboard",
            "price": 100.00,
            "quantity": 10,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    response = authenticated_client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Laptop"
    assert data[1]["name"] == "Keyboard"


def test_update_product(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    create_response = authenticated_client.post(
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

    product_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/products/{product_id}",
        json={
            "name": "Gaming Laptop",
            "price": 1800.00,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Gaming Laptop"
    assert data["description"] == "Development laptop"
    assert data["price"] == 1800.00
    assert data["quantity"] == 10
    assert data["owner_id"] == test_data["user"].id
    assert data["category_id"] == test_data["category"].id


def test_delete_product(
    admin_client: TestClient, test_data: dict[str, User | Category]
):
    create_response = admin_client.post(
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

    product_id = create_response.json()["id"]

    response = admin_client.delete(f"/products/{product_id}")

    assert response.status_code == 204
    assert response.content == b""

    get_response = admin_client.get(f"/products/{product_id}")

    assert get_response.status_code == 404


def test_create_product_validation(
    authenticated_client: TestClient, test_data: dict[str, User | Category]
):
    response = authenticated_client.post(
        "/products",
        json={
            "name": "",
            "description": "Invalid product",
            "price": -100,
            "quantity": -1,
            "owner_id": test_data["user"].id,
            "category_id": test_data["category"].id,
        },
    )

    assert response.status_code == 422


def test_create_product_owner_not_found(authenticated_client: TestClient):
    response = authenticated_client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "quantity": 10,
            "owner_id": 999,
            "category_id": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Owner not found"


def test_create_product_category_not_found(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    response = authenticated_client.post(
        "/products",
        json={
            "name": "Laptop",
            "description": "Development laptop",
            "price": 1200.00,
            "quantity": 10,
            "owner_id": test_data["user"].id,
            "category_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_product_owner_not_found(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    create_response = authenticated_client.post(
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

    product_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/products/{product_id}",
        json={
            "owner_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Owner not found"


def test_update_product_category_not_found(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    create_response = authenticated_client.post(
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

    product_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/products/{product_id}",
        json={
            "category_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_unauthenticated_cannot_update_product(
    client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Test Product",
        description="Test description",
        price=100.0,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.patch(
        f"/products/{product.id}",
        json={"name": "Updated Product"},
    )

    assert response.status_code == 401


def test_unauthenticated_cannot_delete_product(
    client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Test Product",
        description="Test description",
        price=100.0,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.delete(f"/products/{product.id}")

    assert response.status_code == 401


def test_normal_user_cannot_delete_product(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Test Product",
        description="Test description",
        price=100.0,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.delete(f"/products/{product.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_authenticated_user_can_add_stock(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/add",
        json={"quantity": 5},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 15


def test_authenticated_user_can_remove_stock(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 7


def test_unauthenticated_cannot_add_stock(
    client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.post(
        f"/products/{product.id}/stock/add",
        json={"quantity": 5},
    )

    assert response.status_code == 401


def test_unauthenticated_cannot_remove_stock(
    client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": 3},
    )

    assert response.status_code == 401


def test_remove_stock_fails_when_insufficient_stock(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=5,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": 6},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"

    db_session.refresh(product)
    assert product.quantity == 5


def test_add_stock_rejects_invalid_quantity(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/add",
        json={"quantity": 0},
    )

    assert response.status_code == 422

    response = authenticated_client.post(
        f"/products/{product.id}/stock/add",
        json={"quantity": -5},
    )

    assert response.status_code == 422


def test_remove_stock_rejects_invalid_quantity(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    user = test_data["user"]
    category = test_data["category"]

    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": 0},
    )

    assert response.status_code == 422

    response = authenticated_client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": -5},
    )

    assert response.status_code == 422


def test_add_stock_returns_404_for_missing_product(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/products/999/stock/add",
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_remove_stock_returns_404_for_missing_product(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/products/999/stock/remove",
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_not_found(
    authenticated_client: TestClient,
):
    response = authenticated_client.patch(
        "/products/999",
        json={"name": "Updated Product"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_invalid_data(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    create_response = authenticated_client.post(
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

    product_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/products/{product_id}",
        json={
            "price": -100,
        },
    )

    assert response.status_code == 422


def test_remove_stock_to_zero(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
):
    product = Product(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=5,
        owner_id=test_data["user"].id,
        category_id=test_data["category"].id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        f"/products/{product.id}/stock/remove",
        json={"quantity": 5},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 0

    db_session.refresh(product)
    assert product.quantity == 0
