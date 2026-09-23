from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, product_id: int) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Product]:
        statement = select(Product)
        return list(self.session.scalars(statement).all())

    def create(
        self,
        name: str,
        description: str | None,
        price: float,
        quantity: int,
        owner_id: int,
        category_id: int,
    ) -> Product:
        product = Product(
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            owner_id=owner_id,
            category_id=category_id,
        )
        self.session.add(product)
        self.session.flush()

        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)
        self.session.flush()

    def update(
        self,
        product: Product,
        name: str | None,
        description: str | None,
        price: float | None,
        quantity: int | None,
        owner_id: int | None,
        category_id: int | None,
    ) -> Product:
        if name is not None:
            product.name = name

        if description is not None:
            product.description = description

        if price is not None:
            product.price = price

        if quantity is not None:
            product.quantity = quantity

        if owner_id is not None:
            product.owner_id = owner_id

        if category_id is not None:
            product.category_id = category_id

        self.session.flush()

        return product
