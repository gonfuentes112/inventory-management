from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.product import Product


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_order(
        self,
        user_id: int,
        status: str,
        total: Decimal,
    ) -> Order:
        order = Order(
            user_id=user_id,
            status=status,
            total=total,
        )
        self.session.add(order)
        self.session.flush()
        return order

    def create_order_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
        subtotal: Decimal,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get_product_for_update(
        self,
        product_id: int,
    ) -> Product | None:
        statement = select(Product).where(Product.id == product_id).with_for_update()
        return self.session.scalar(statement)

    def get_by_id(
        self,
        order_id: int,
        user_id: int,
    ) -> Order | None:
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        return self.session.scalar(statement)
