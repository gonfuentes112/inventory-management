from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_order(
        self,
        user_id: int,
        total: Decimal,
        status: str = "pending",
    ) -> Order:
        order = Order(
            user_id=user_id,
            total=total,
            status=status,
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

    def get_by_id(self, order_id: int) -> Order | None:
        statement = (
            select(Order)
            .where(Order.id == order_id)
        )
        return self.session.scalar(statement)

    def get_by_user(
        self,
        user_id: int,
    ) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
        )
        return list(self.session.scalars(statement).all())