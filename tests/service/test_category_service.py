from app.services.category import CategoryService
from sqlalchemy.orm import Session


def test_create_category(db_session: Session):
    service = CategoryService(db_session)

    category = service.create_category("Electronics")

    assert category.id is not None
    assert category.name == "Electronics"


def test_get_category(db_session: Session):
    service = CategoryService(db_session)

    created = service.create_category("Electronics")
    category = service.get_category(created.id)

    assert category is not None
    assert category.id == created.id
    assert category.name == "Electronics"


def test_get_categories(db_session: Session):
    service = CategoryService(db_session)

    service.create_category("Electronics")
    service.create_category("Books")

    categories = service.get_categories()

    assert len(categories) == 2
    assert {category.name for category in categories} == {
        "Electronics",
        "Books",
    }


def test_delete_category(db_session: Session):
    service = CategoryService(db_session)

    category = service.create_category("Electronics")

    deleted = service.delete_category(category.id)

    assert deleted is True
    assert service.get_category(category.id) is None


def test_delete_category_not_found(db_session: Session):
    service = CategoryService(db_session)

    deleted = service.delete_category(999)

    assert deleted is False
