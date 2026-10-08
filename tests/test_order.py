from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order import OrderService

from tests.conftest import ProductTestData


def create_product(
    db_session: Session,
    *,
    user: User,
    category_id: int,
    name: str,
    price: Decimal,
    quantity: int,
) -> Product:
    product = Product(
        name=name,
        description=None,
        price=price,
        quantity=quantity,
        owner_id=user.id,
        category_id=category_id,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


def test_create_order(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    user = test_data["user"]
    category = test_data["category"]

    product = create_product(
        db_session,
        user=user,
        category_id=category.id,
        name="Keyboard",
        price=Decimal("1200.00"),
        quantity=10,
    )

    service = OrderService(db_session)

    data = OrderCreate(
        items=[
            OrderItemCreate(
                product_id=product.id,
                quantity=2,
            )
        ]
    )

    order = service.create_order(
        data=data,
        current_user_id=user.id,
    )

    assert order.id is not None
    assert order.user_id == user.id
    assert order.status == "pending"
    assert order.total == Decimal("2400.00")

    db_session.refresh(product)

    assert product.quantity == 8

    assert len(order.items) == 1

    item = order.items[0]

    assert item.product_id == product.id
    assert item.quantity == 2
    assert item.unit_price == Decimal("1200.00")
    assert item.subtotal == Decimal("2400.00")


def test_create_order_with_multiple_products(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    user = test_data["user"]
    category = test_data["category"]

    product_1 = create_product(
        db_session,
        user=user,
        category_id=category.id,
        name="Keyboard",
        price=Decimal("1200.00"),
        quantity=10,
    )

    product_2 = create_product(
        db_session,
        user=user,
        category_id=category.id,
        name="Mouse",
        price=Decimal("800.00"),
        quantity=5,
    )

    service = OrderService(db_session)

    data = OrderCreate(
        items=[
            OrderItemCreate(
                product_id=product_1.id,
                quantity=2,
            ),
            OrderItemCreate(
                product_id=product_2.id,
                quantity=3,
            ),
        ]
    )

    order = service.create_order(
        data=data,
        current_user_id=user.id,
    )

    assert order.total == Decimal("4800.00")
    assert len(order.items) == 2

    db_session.refresh(product_1)
    db_session.refresh(product_2)

    assert product_1.quantity == 8
    assert product_2.quantity == 2


def test_insufficient_stock_rolls_back(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    user = test_data["user"]
    category = test_data["category"]

    product = create_product(
        db_session,
        user=user,
        category_id=category.id,
        name="Keyboard",
        price=Decimal("1200.00"),
        quantity=2,
    )

    service = OrderService(db_session)

    data = OrderCreate(
        items=[
            OrderItemCreate(
                product_id=product.id,
                quantity=3,
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Insufficient stock",
    ):
        service.create_order(
            data=data,
            current_user_id=user.id,
        )

    db_session.refresh(product)

    assert product.quantity == 2
    assert db_session.query(Order).count() == 0


def test_product_not_found_rolls_back(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    user = test_data["user"]

    service = OrderService(db_session)

    data = OrderCreate(
        items=[
            OrderItemCreate(
                product_id=999999,
                quantity=1,
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Product 999999 not found",
    ):
        service.create_order(
            data=data,
            current_user_id=user.id,
        )

    assert db_session.query(Order).count() == 0


def test_duplicate_product_is_rejected(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    user = test_data["user"]
    category = test_data["category"]

    product = create_product(
        db_session,
        user=user,
        category_id=category.id,
        name="Keyboard",
        price=Decimal("1200.00"),
        quantity=10,
    )

    service = OrderService(db_session)

    data = OrderCreate(
        items=[
            OrderItemCreate(
                product_id=product.id,
                quantity=1,
            ),
            OrderItemCreate(
                product_id=product.id,
                quantity=2,
            ),
        ]
    )

    with pytest.raises(
        ValueError,
        match=f"Duplicate product: {product.id}",
    ):
        service.create_order(
            data=data,
            current_user_id=user.id,
        )

    db_session.refresh(product)

    assert product.quantity == 10
    assert db_session.query(Order).count() == 0
