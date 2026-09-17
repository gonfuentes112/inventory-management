from app.models.category import Category
from app.models.user import User
from app.repositories.product import ProductRepository


def test_create_product(db_session):
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


def test_get_product_by_id(db_session):
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


def test_get_product_by_id_returns_none_when_not_found(db_session):
    repository = ProductRepository(db_session)

    result = repository.get_by_id(999)

    assert result is None


def test_get_all_products(db_session):
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
