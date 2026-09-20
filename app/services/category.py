from sqlalchemy.orm import Session
from app.repositories.category import CategoryRespository

from app.models.category import Category


class CategoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CategoryRespository(session)

    def create_category(self, name: str) -> Category:
        category = self.repository.create(name)
        self.session.commit()
        self.session.refresh(category)

        return category

    def get_category(self, category_id: int) -> Category | None:
        return self.repository.get_by_id(category_id)

    def get_categories(self) -> list[Category]:
        return self.repository.get_all()

    def delete_category(self, category_id: int) -> bool:
        category = self.repository.get_by_id(category_id)

        if category is None:
            return False

        self.repository.delete(category)
        self.session.commit()
        return True
