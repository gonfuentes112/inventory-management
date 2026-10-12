"""Order cancellation and business-error types.

Marked `postgres` because cancellation relies on row locks (SELECT ... FOR
UPDATE), which SQLite ignores.
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateProductError,
    InsufficientStockError,
    InvalidOrderStateError,
    OrderNotFoundError,
    ProductNotFoundError,
)
from app.core.security import hash_password
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_PENDING,
    OrderService,
)

BARRIER_TIMEOUT_SECONDS = 30


def _seed(session: Session, *, quantities: list[int]) -> tuple[list[int], list[int]]:
    """Create one category, two users and one product per quantity.

    Returns (product_ids, [user_id_1, user_id_2]).
    """
    suffix = uuid4().hex[:8]

    category = Category(name=f"Cancel Test Category {suffix}")
    users = [
        User(
            username=f"cancel_user_{i}_{suffix}",
            email=f"cancel_{i}_{suffix}@example.com",
            hashed_password=hash_password("testpassword123"),
            role="user",
        )
        for i in range(2)
    ]
    session.add_all([category, *users])
    session.commit()

    products = [
        Product(
            name=f"Cancel Test Product {i}_{suffix}",
            description=None,
            price=Decimal("25.00"),
            quantity=quantity,
            owner_id=users[0].id,
            category_id=category.id,
        )
        for i, quantity in enumerate(quantities)
    ]
    session.add_all(products)
    session.commit()

    return [p.id for p in products], [u.id for u in users]


def _create_order(engine, user_id: int, items: list[tuple[int, int]]) -> int:
    data = OrderCreate(
        items=[OrderItemCreate(product_id=pid, quantity=qty) for pid, qty in items]
    )
    with Session(engine) as session:
        order = OrderService(session).create_order(data=data, current_user_id=user_id)
        return order.id


def _cancel(engine, user_id: int, order_id: int):
    with Session(engine) as session:
        order = OrderService(session).cancel_order(order_id, current_user_id=user_id)
        return order.status


def _quantity(session: Session, product_id: int) -> int:
    session.expire_all()
    product = session.scalar(select(Product).where(Product.id == product_id))
    assert product is not None
    return product.quantity


@pytest.mark.postgres
def test_cancel_restores_stock_and_marks_order_cancelled(
    postgres_session: Session,
) -> None:
    (product_a, product_b), (user_id, _) = _seed(postgres_session, quantities=[10, 5])
    engine = postgres_session.get_bind().engine

    order_id = _create_order(engine, user_id, [(product_a, 3), (product_b, 2)])
    assert _quantity(postgres_session, product_a) == 7
    assert _quantity(postgres_session, product_b) == 3

    status = _cancel(engine, user_id, order_id)

    assert status == ORDER_STATUS_CANCELLED
    assert _quantity(postgres_session, product_a) == 10
    assert _quantity(postgres_session, product_b) == 5


@pytest.mark.postgres
def test_cancelling_twice_is_rejected_and_stock_is_restored_once(
    postgres_session: Session,
) -> None:
    (product_id,), (user_id, _) = _seed(postgres_session, quantities=[10])
    engine = postgres_session.get_bind().engine

    order_id = _create_order(engine, user_id, [(product_id, 4)])
    _cancel(engine, user_id, order_id)

    with pytest.raises(InvalidOrderStateError):
        _cancel(engine, user_id, order_id)

    assert _quantity(postgres_session, product_id) == 10


@pytest.mark.postgres
def test_user_cannot_cancel_another_users_order(postgres_session: Session) -> None:
    (product_id,), (owner_id, other_id) = _seed(postgres_session, quantities=[10])
    engine = postgres_session.get_bind().engine

    order_id = _create_order(engine, owner_id, [(product_id, 4)])

    with pytest.raises(OrderNotFoundError):
        _cancel(engine, other_id, order_id)

    # Order and stock are untouched.
    assert _quantity(postgres_session, product_id) == 6
    assert _cancel(engine, owner_id, order_id) == ORDER_STATUS_CANCELLED


@pytest.mark.postgres
def test_concurrent_double_cancel_restores_stock_only_once(
    postgres_session: Session,
) -> None:
    (product_id,), (user_id, _) = _seed(postgres_session, quantities=[10])
    engine = postgres_session.get_bind().engine

    order_id = _create_order(engine, user_id, [(product_id, 4)])
    barrier = Barrier(2)

    def worker() -> str:
        with Session(engine) as session:
            service = OrderService(session)
            barrier.wait(timeout=BARRIER_TIMEOUT_SECONDS)
            try:
                service.cancel_order(order_id, current_user_id=user_id)
                return "success"
            except InvalidOrderStateError:
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker) for _ in range(2)]
        results = [future.result() for future in futures]

    assert sorted(results) == ["rejected", "success"]
    # 10 - 4 + 4 = 10. Restoring twice would leave 14.
    assert _quantity(postgres_session, product_id) == 10


@pytest.mark.postgres
def test_business_errors_use_specific_exception_types(
    postgres_session: Session,
) -> None:
    (product_id,), (user_id, _) = _seed(postgres_session, quantities=[2])
    engine = postgres_session.get_bind().engine

    with pytest.raises(InsufficientStockError):
        _create_order(engine, user_id, [(product_id, 3)])

    with pytest.raises(ProductNotFoundError):
        _create_order(engine, user_id, [(product_id + 1_000_000, 1)])

    with pytest.raises(DuplicateProductError):
        _create_order(engine, user_id, [(product_id, 1), (product_id, 1)])

    # All three are still ValueErrors, so older `except ValueError` code works.
    with pytest.raises(ValueError):
        _create_order(engine, user_id, [(product_id, 3)])

    # A new order is created as pending.
    order_id = _create_order(engine, user_id, [(product_id, 1)])
    with Session(engine) as session:
        order = OrderService(session).get_order(order_id, current_user_id=user_id)
        assert order is not None
        assert order.status == ORDER_STATUS_PENDING
