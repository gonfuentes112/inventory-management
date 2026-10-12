from decimal import Decimal

from sqlalchemy.orm import Session

from app.cache.product import delete_cached_product
from app.core.exceptions import (
    DuplicateProductError,
    InsufficientStockError,
    InvalidOrderStateError,
    OrderNotFoundError,
    ProductNotFoundError,
)
from app.models.order import Order
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate

ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_CANCELLED = "cancelled"


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = OrderRepository(session)

    def create_order(
        self,
        data: OrderCreate,
        *,
        current_user_id: int,
    ):
        locked_products = {}

        try:
            product_ids = [item.product_id for item in data.items]

            if len(product_ids) != len(set(product_ids)):
                duplicate_product_id = next(
                    product_id
                    for product_id in product_ids
                    if product_ids.count(product_id) > 1
                )

                raise DuplicateProductError(
                    f"Duplicate product: {duplicate_product_id}"
                )
            for product_id in sorted(product_ids):
                product = self.repository.get_product_for_update(product_id)

                if product is None:
                    raise ProductNotFoundError(f"Product {product_id} not found")

                locked_products[product_id] = product

            for item in data.items:
                product = locked_products[item.product_id]

                if product.quantity < item.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for product {item.product_id}"
                    )

            total = Decimal("0.00")
            order_items = []

            for item in data.items:
                product = locked_products[item.product_id]

                unit_price = product.price
                subtotal = unit_price * item.quantity

                product.quantity -= item.quantity
                total += subtotal

                order_items.append(
                    (
                        product,
                        item.quantity,
                        unit_price,
                        subtotal,
                    )
                )

            order = self.repository.create_order(
                user_id=current_user_id,
                status=ORDER_STATUS_PENDING,
                total=total,
            )

            for (
                product,
                quantity,
                unit_price,
                subtotal,
            ) in order_items:
                self.repository.create_order_item(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(order)

        for product, _, _, _ in order_items:
            delete_cached_product(product.id)

        return order

    def cancel_order(
        self,
        order_id: int,
        *,
        current_user_id: int,
    ) -> Order:
        restored_product_ids: list[int] = []

        try:
            order = self.repository.get_by_id_for_update(
                order_id=order_id,
                user_id=current_user_id,
            )

            if order is None:
                raise OrderNotFoundError("Order not found")

            if order.status != ORDER_STATUS_PENDING:
                raise InvalidOrderStateError(
                    f"Order cannot be cancelled because its status is '{order.status}'"
                )

            quantities: dict[int, int] = {}
            for item in order.items:
                quantities[item.product_id] = (
                    quantities.get(item.product_id, 0) + item.quantity
                )

            for product_id in sorted(quantities):
                product = self.repository.get_product_for_update(product_id)

                if product is None:
                    raise ProductNotFoundError(f"Product {product_id} not found")

                product.quantity += quantities[product_id]
                restored_product_ids.append(product_id)

            order.status = ORDER_STATUS_CANCELLED

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(order)

        for product_id in restored_product_ids:
            delete_cached_product(product_id)

        return order

    def get_order(
        self,
        order_id: int,
        *,
        current_user_id: int,
    ):
        return self.repository.get_by_id(
            order_id=order_id,
            user_id=current_user_id,
        )

    def get_orders_paginated(
        self,
        *,
        current_user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        return self.repository.get_paginated_by_user(
            user_id=current_user_id,
            page=page,
            page_size=page_size,
        )
