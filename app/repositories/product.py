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
        owner_id: int,
        category_id: int,
    ) -> Product:
        product = Product(
            name=name,
            description=description,
            price=price,
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
        name: str,
        description: str | None,
        price: float,
        owner_id: int,
        category_id: int,
    ) -> Product:
        product.name = name
        product.description = description
        product.price = price
        product.owner_id = owner_id
        product.category_id = category_id

        self.session.flush()
        return product
