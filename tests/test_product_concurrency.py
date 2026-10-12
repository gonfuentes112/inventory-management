from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.services.product import ProductService


def _create_product(session: Session, quantity: int) -> tuple[int, int]:
    suffix = uuid4().hex[:8]

    category = Category(name=f"Stock Concurrency Category {suffix}")
    owner = User(
        username=f"stock_owner_{suffix}",
        email=f"stock_owner_{suffix}@example.com",
        hashed_password=hash_password("testpassword123"),
        role="user",
    )
    session.add_all([category, owner])
    session.commit()

    product = Product(
        name=f"Stock Concurrency Product {suffix}",
        description=None,
        price=Decimal("10.00"),
        quantity=quantity,
        owner_id=owner.id,
        category_id=category.id,
    )
    session.add(product)
    session.commit()

    return product.id, owner.id


def _run_concurrently(
    engine, product_id: int, owner_id: int, operation: str, amount: int, workers: int
) -> list[str]:
    barrier = Barrier(workers)

    def worker() -> str:
        with Session(engine) as session:
            service = ProductService(session)
            barrier.wait()
            try:
                method = getattr(service, operation)
                method(
                    product_id,
                    amount,
                    current_user_id=owner_id,
                    is_admin=False,
                )
                return "success"
            except ValueError:
                return "insufficient_stock"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker) for _ in range(workers)]
        return [f.result() for f in futures]


def _final_quantity(session: Session, product_id: int) -> int:
    session.expire_all()
    product = session.scalar(select(Product).where(Product.id == product_id))
    assert product is not None
    return product.quantity


@pytest.mark.postgres
def test_concurrent_add_stock_does_not_lose_updates(postgres_session: Session) -> None:
    product_id, owner_id = _create_product(postgres_session, quantity=0)
    engine = postgres_session.get_bind().engine

    results = _run_concurrently(
        engine, product_id, owner_id, "add_stock", 5, workers=10
    )

    assert results == ["success"] * 10
    assert _final_quantity(postgres_session, product_id) == 50


@pytest.mark.postgres
def test_concurrent_remove_stock_cannot_oversell(postgres_session: Session) -> None:
    product_id, owner_id = _create_product(postgres_session, quantity=5)
    engine = postgres_session.get_bind().engine

    results = _run_concurrently(
        engine, product_id, owner_id, "remove_stock", 1, workers=10
    )

    assert results.count("success") == 5
    assert results.count("insufficient_stock") == 5
    assert _final_quantity(postgres_session, product_id) == 0
