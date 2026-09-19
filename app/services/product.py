from sqlalchemy.orm import Session

from app.repositories.product import ProductRepository

from app.models.product import Product

from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: Session) -> None:
        self.repository = ProductRepository(session)

    def create_product(self, data: ProductCreate) -> Product:
        return self.repository.create(
            name=data.name,
            description=data.description,
            price=data.price,
            owner_id=data.owner_id,
            category_id=data.category_id,
        )

    def get_product(self, product_id: int) -> Product | None:
        return self.repository.get_by_id(product_id)

    def get_products(self) -> list[Product]:
        return self.repository.get_all()

    def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> Product | None:
        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        return self.repository.update(
            product,
            name=data.name,
            description=data.description,
            price=data.price,
            owner_id=data.owner_id,
            category_id=data.category_id,
        )

    def delete_product(self, product: Product) -> None:
        return self.repository.delete(product)
