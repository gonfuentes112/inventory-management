from app.models.category import Category
from app.models.user import User
from app.repositories.product import ProductRepository

from sqlalchemy.orm import Session


def test_create_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add(user)
    db_session.add(category)
    db_session.commit()

    repository = ProductRepository(db_session)

    product = repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    assert product.name == "Laptop"
    assert product.description == "Development laptop"
    assert product.price == 1200.00
    assert product.owner_id == user.id
    assert product.category_id == category.id


def test_get_product_by_id(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    repository = ProductRepository(db_session)

    product = repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    result = repository.get_by_id(product.id)

    assert result is not None
    assert result.id == product.id
    assert result.name == "Laptop"


def test_get_product_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repository = ProductRepository(db_session)

    result = repository.get_by_id(999)

    assert result is None


def test_get_all_products(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    repository = ProductRepository(db_session)

    repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    repository.create(
        name="Keyboard",
        description="Mechanical keyboard",
        price=100.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    products = repository.get_all()

    assert len(products) == 2
    assert products[0].name == "Laptop"
    assert products[1].name == "Keyboard"


def test_update_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    repository = ProductRepository(db_session)

    product = repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    updated_product = repository.update(
        product=product,
        name="Gaming Laptop",
        description="High-performance development laptop",
        price=1800.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    assert updated_product.name == "Gaming Laptop"
    assert updated_product.description == "High-performance development laptop"
    assert updated_product.price == 1800.00
    assert updated_product.category_id == category.id


def test_delete_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    repository = ProductRepository(db_session)

    product = repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    repository.delete(product)
    db_session.commit()

    result = repository.get_by_id(product.id)

    assert result is None


def test_update_product_partial(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    repository = ProductRepository(db_session)

    product = repository.create(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        owner_id=user.id,
        category_id=category.id,
    )

    db_session.commit()

    updated_product = repository.update(
        product=product,
        name="Gaming Laptop",
        description=None,
        price=None,
        owner_id=None,
        category_id=None,
    )

    db_session.commit()

    assert updated_product.name == "Gaming Laptop"
    assert updated_product.description == "Development laptop"
    assert updated_product.price == 1200.00
    assert updated_product.owner_id == user.id
    assert updated_product.category_id == category.id
