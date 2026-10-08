from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.category import Category
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order import OrderService

from uuid import uuid4

test_id = uuid4().hex[:8]


@pytest.mark.postgres
def test_concurrent_orders_cannot_oversell_stock(
    postgres_session: Session,
) -> None:
    category = Category(
        name=f"Concurrency Test Category {test_id}",
    )

    user_1 = User(
        username=f"concurrency_user_1_{test_id}",
        email=f"concurrency1_{test_id}@example.com",
        hashed_password=hash_password("testpassword123"),
        role="user",
    )

    user_2 = User(
        username=f"concurrency_user_2_{test_id}",
        email=f"concurrency2_{test_id}@example.com",
        hashed_password=hash_password("testpassword123"),
        role="user",
    )

    postgres_session.add_all(
        [
            category,
            user_1,
            user_2,
        ]
    )
    postgres_session.commit()

    product = Product(
        name="Concurrency Test Product",
        description=None,
        price=Decimal("100.00"),
        quantity=1,
        owner_id=user_1.id,
        category_id=category.id,
    )

    postgres_session.add(product)
    postgres_session.commit()
    postgres_session.refresh(product)

    product_id = product.id
    user_1_id = user_1.id
    user_2_id = user_2.id

    engine = postgres_session.get_bind().engine

    def create_order(user_id: int) -> str:
        with Session(engine) as session:
            service = OrderService(session)

            data = OrderCreate(
                items=[
                    OrderItemCreate(
                        product_id=product_id,
                        quantity=1,
                    )
                ]
            )

            try:
                service.create_order(
                    data=data,
                    current_user_id=user_id,
                )
                return "success"
            except ValueError:
                return "insufficient_stock"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                create_order,
                [user_1_id, user_2_id],
            )
        )

    assert sorted(results) == [
        "insufficient_stock",
        "success",
    ]

    postgres_session.expire_all()

    final_product = postgres_session.scalar(
        select(Product).where(Product.id == product_id)
    )

    assert final_product is not None
    assert final_product.quantity == 0

    orders = postgres_session.scalars(
        select(Order).where(Order.user_id.in_([user_1_id, user_2_id]))
    ).all()

    assert len(orders) == 1
