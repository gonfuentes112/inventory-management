from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRespository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, category_id: int) -> Category | None:
        statement = select(Category).where(Category.id == category_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Category]:
        statement = select(Category)
        return list(self.session.scalars(statement).all())

    def create(self, name: str) -> Category:
        category = Category(name=name)

        self.session.add(category)
        self.session.flush()

        return category

    def delete(self, category: Category) -> None:
        self.session.delete(category)
        self.session.flush()
