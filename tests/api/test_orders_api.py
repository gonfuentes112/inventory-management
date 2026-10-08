from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.security import hash_password
from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.category import Category
from app.models.user import User

from app.main import app


def create_product(
    authenticated_client: TestClient,
    *,
    category_id: int,
    name: str,
    price: float = 100.00,
    quantity: int = 10,
) -> dict:
    response = authenticated_client.post(
        "/products",
        json={
            "name": name,
            "description": name,
            "price": price,
            "quantity": quantity,
            "category_id": category_id,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_order(
    authenticated_client: TestClient,
    *,
    product_id: int,
    quantity: int = 1,
) -> dict:
    response = authenticated_client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            ]
        },
    )

    assert response.status_code == 201

    return response.json()


def test_create_order(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
) -> None:
    category = test_data["category"]
    user = test_data["user"]

    product = Product(
        name="Order Product",
        description="Product for order test",
        price=Decimal("25.00"),
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = authenticated_client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                }
            ]
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user.id
    assert data["status"] == "pending"
    assert data["total"] == "50.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product.id
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == "25.00"
    assert data["items"][0]["subtotal"] == "50.00"

    db_session.expire_all()

    updated_product = db_session.get(Product, product.id)

    assert updated_product is not None
    assert updated_product.quantity == 8


def test_get_orders_pagination(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    category = test_data["category"]

    for i in range(5):
        product = create_product(
            authenticated_client,
            category_id=category.id,
            name=f"Order Product {i}",
        )

        create_order(
            authenticated_client,
            product_id=product["id"],
        )

    response = authenticated_client.get("/orders?page=1&page_size=2")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2


def test_get_orders_second_page(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    category = test_data["category"]

    for i in range(5):
        product = create_product(
            authenticated_client,
            category_id=category.id,
            name=f"Order Product {i}",
        )

        create_order(
            authenticated_client,
            product_id=product["id"],
        )

    response = authenticated_client.get("/orders?page=2&page_size=2")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2

    # Orders are sorted newest first.
    assert data["items"][0]["id"] > data["items"][1]["id"]


def test_get_orders_invalid_pagination(
    authenticated_client: TestClient,
):
    response = authenticated_client.get("/orders?page=0")

    assert response.status_code == 422

    response = authenticated_client.get("/orders?page_size=0")

    assert response.status_code == 422

    response = authenticated_client.get("/orders?page_size=101")

    assert response.status_code == 422


def test_get_order(
    authenticated_client: TestClient,
    test_data: dict[str, User | Category],
):
    product = create_product(
        authenticated_client,
        category_id=test_data["category"].id,
        name="Order Retrieval Product",
        price=1200.00,
    )

    order = create_order(
        authenticated_client,
        product_id=product["id"],
        quantity=2,
    )

    response = authenticated_client.get(f"/orders/{order['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order["id"]
    assert data["user_id"] == test_data["user"].id
    assert data["status"] == "pending"
    assert data["total"] == "2400.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product["id"]
    assert data["items"][0]["quantity"] == 2


def test_user_cannot_access_another_users_order(
    authenticated_client: TestClient,
    db_session: Session,
    test_data: dict[str, User | Category],
) -> None:
    category = test_data["category"]

    product = create_product(
        authenticated_client,
        category_id=category.id,
        name="Authorization Test Product",
    )

    order = create_order(
        authenticated_client,
        product_id=product["id"],
    )

    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=hash_password("otherpassword123"),
        role="user",
    )
    db_session.add(other_user)
    db_session.commit()

    other_client = TestClient(app)

    response = other_client.post(
        "/users/login",
        json={
            "username": "otheruser",
            "password": "otherpassword123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]
    other_client.headers.update({"Authorization": f"Bearer {token}"})

    response = other_client.get(f"/orders/{order['id']}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
