from decimal import Decimal
from sqlalchemy import select, func
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

    def get_paginated(
        self,
        *,
        page: int,
        page_size: int,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Product], int]:
        filters = []

        if category_id is not None:
            filters.append(Product.category_id == category_id)

        if min_price is not None:
            filters.append(Product.price >= min_price)

        if max_price is not None:
            filters.append(Product.price <= max_price)

        total_statement = select(func.count()).select_from(Product).where(*filters)

        total = self.session.scalar(total_statement) or 0

        sort_columns = {
            "id": Product.id,
            "name": Product.name,
            "price": Product.price,
            "quantity": Product.quantity,
        }

        sort_column = sort_columns[sort_by]

        if sort_order == "desc":
            order_expression = sort_column.desc()
        else:
            order_expression = sort_column.asc()

        offset = (page - 1) * page_size

        statement = (
            select(Product)
            .where(*filters)
            .order_by(order_expression, Product.id)
            .offset(offset)
            .limit(page_size)
        )

        products = list(self.session.scalars(statement).all())

        return products, total

    def create(
        self,
        name: str,
        description: str | None,
        price: Decimal,
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
        price: Decimal | None,
        quantity: int | None,
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

        if category_id is not None:
            product.category_id = category_id

        self.session.flush()

        return product
