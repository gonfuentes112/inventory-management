from sqlalchemy.orm import Session

from app.repositories.product import ProductRepository

from app.models.product import Product

from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

from app.repositories.user import UserRepository
from app.repositories.category import CategoryRepository

from app.cache.product import cache_product, get_cached_product, delete_cached_product


class ProductService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ProductRepository(session)
        self.user_repository = UserRepository(session)
        self.category_repository = CategoryRepository(session)

    def create_product(self, data: ProductCreate) -> Product:
        if self.user_repository.get_by_id(data.owner_id) is None:
            raise ValueError("Owner not found")

        if self.category_repository.get_by_id(data.category_id) is None:
            raise ValueError("Category not found")
        product = self.repository.create(
            name=data.name,
            description=data.description,
            price=data.price,
            quantity=data.quantity,
            owner_id=data.owner_id,
            category_id=data.category_id,
        )
        self.session.commit()
        self.session.refresh(product)

        return product

    def get_product(self, product_id: int) -> Product | None:
        cached_product = get_cached_product(product_id)

        if cached_product is not None:
            return Product(
                id=cached_product.id,
                name=cached_product.name,
                description=cached_product.description,
                price=cached_product.price,
                quantity=cached_product.quantity,
                owner_id=cached_product.owner_id,
                category_id=cached_product.category_id,
            )

        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        cache_product(ProductResponse.model_validate(product))

        return product

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

        if data.owner_id is not None:
            if self.user_repository.get_by_id(data.owner_id) is None:
                raise ValueError("Owner not found")

        if data.category_id is not None:
            if self.category_repository.get_by_id(data.category_id) is None:
                raise ValueError("Category not found")

        self.repository.update(
            product,
            name=data.name,
            description=data.description,
            price=data.price,
            quantity=data.quantity,
            owner_id=data.owner_id,
            category_id=data.category_id,
        )
        self.session.commit()
        self.session.refresh(product)

        delete_cached_product(product_id)

        return product

    def delete_product(
        self,
        product_id: int,
    ) -> bool:
        product = self.repository.get_by_id(product_id)

        if product is None:
            return False

        self.repository.delete(product)
        self.session.commit()

        delete_cached_product(product_id)

        return True

    def add_stock(
        self,
        product_id: int,
        quantity: int,
    ) -> Product | None:
        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        product.quantity += quantity

        self.session.commit()
        self.session.refresh(product)

        delete_cached_product(product_id)

        return product

    def remove_stock(
        self,
        product_id: int,
        quantity: int,
    ) -> Product | None:
        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        if product.quantity < quantity:
            raise ValueError("Insufficient stock")

        product.quantity -= quantity

        self.session.commit()
        self.session.refresh(product)

        delete_cached_product(product_id)

        return product
