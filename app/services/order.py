from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.order import Order

from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate
from app.cache.product import delete_cached_product


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

                raise ValueError(f"Duplicate product: {duplicate_product_id}")

            for product_id in sorted(product_ids):
                product = self.repository.get_product_for_update(product_id)

                if product is None:
                    raise ValueError(f"Product {product_id} not found")

                locked_products[product_id] = product

            for item in data.items:
                product = locked_products[item.product_id]

                if product.quantity < item.quantity:
                    raise ValueError(
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
                status="pending",
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

    def get_orders(
        self,
        *,
        current_user_id: int,
    ) -> list[Order]:
        return self.repository.get_all_by_user(
            user_id=current_user_id,
        )
