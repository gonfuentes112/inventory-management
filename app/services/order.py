from decimal import Decimal

from sqlalchemy.orm import Session

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
            for item in data.items:
                if item.product_id in locked_products:
                    raise ValueError(f"Duplicate product: {item.product_id}")

                product = self.repository.get_product_for_update(item.product_id)

                if product is None:
                    raise ValueError(f"Product {item.product_id} not found")

                if product.quantity < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for product {item.product_id}"
                    )

                locked_products[item.product_id] = product

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
