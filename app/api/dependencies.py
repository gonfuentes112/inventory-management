from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.product import ProductService
from app.services.category import CategoryService
from app.services.user import UserService


def get_product_service(
    db: Annotated[Session, Depends(get_db)],
) -> ProductService:
    return ProductService(db)


def get_category_service(db: Annotated[Session, Depends(get_db)]) -> CategoryService:
    return CategoryService(db)


def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)
