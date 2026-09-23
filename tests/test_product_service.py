from pytest import raises

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product import ProductService


def test_create_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    data = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    product = service.create_product(data)

    assert product.id is not None
    assert product.name == "Laptop"
    assert product.description == "Development laptop"
    assert product.price == 1200.00
    assert product.owner_id == user.id
    assert product.category_id == category.id


def test_get_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    data = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=category.id,
    )

    created_product = service.create_product(data)

    product = service.get_product(created_product.id)

    assert product is not None
    assert product.id == created_product.id
    assert product.name == "Laptop"


def test_get_product_returns_none_when_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)

    product = service.get_product(999)

    assert product is None


def test_get_products(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    service.create_product(
        ProductCreate(
            name="Keyboard",
            description="Mechanical keyboard",
            price=100.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    products = service.get_products()

    assert len(products) == 2
    assert products[0].name == "Laptop"
    assert products[1].name == "Keyboard"


def test_update_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    updated_product = service.update_product(
        product_id=product.id,
        data=ProductUpdate(
            name="Gaming Laptop",
            description="High-performance laptop",
            price=1800.00,
            owner_id=user.id,
            category_id=category.id,
        ),
    )

    assert updated_product is not None
    assert updated_product.id == product.id
    assert updated_product.name == "Gaming Laptop"
    assert updated_product.description == "High-performance laptop"
    assert updated_product.price == 1800.00
    assert updated_product.owner_id == user.id
    assert updated_product.category_id == category.id


def test_update_product_returns_none_when_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)

    result = service.update_product(
        product_id=999,
        data=ProductUpdate(
            name="Updated Product",
        ),
    )

    assert result is None


def test_delete_product(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    result = service.delete_product(product.id)

    assert result is True
    assert service.get_product(product.id) is None


def test_delete_product_returns_false_when_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)

    result = service.delete_product(999)

    assert result is False


def test_create_product_fails_when_owner_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)
    assert service.user_repository.get_by_id(999) is None

    data = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=999,
        category_id=1,
    )

    assert data.owner_id == 999
    assert data.category_id == 1

    with raises(ValueError, match="Owner not found"):
        service.create_product(data)


def test_create_product_fails_when_category_not_found(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    db_session.add(user)
    db_session.commit()

    service = ProductService(db_session)

    assert service.category_repository.get_by_id(999) is None

    data = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=user.id,
        category_id=999,
    )

    assert data.owner_id == user.id
    assert data.category_id == 999

    with raises(ValueError, match="Category not found"):
        service.create_product(data)


def test_update_product_fails_when_owner_not_found(
    db_session: Session,
    test_data: dict[str, User | Category],
) -> None:
    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=test_data["user"].id,
            category_id=test_data["category"].id,
        )
    )

    with raises(ValueError, match="Owner not found"):
        service.update_product(
            product.id,
            ProductUpdate(owner_id=999),
        )


def test_update_product_fails_when_category_not_found(
    db_session: Session,
    test_data: dict[str, User | Category],
) -> None:
    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=test_data["user"].id,
            category_id=test_data["category"].id,
        )
    )

    with raises(ValueError, match="Category not found"):
        service.update_product(
            product.id,
            ProductUpdate(category_id=999),
        )


def test_add_stock(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    updated_product = service.add_stock(
        product_id=product.id,
        quantity=5,
    )

    assert updated_product is not None
    assert updated_product.quantity == 15


def test_remove_stock(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    updated_product = service.remove_stock(
        product_id=product.id,
        quantity=3,
    )

    assert updated_product is not None
    assert updated_product.quantity == 7


def test_remove_stock_fails_when_insufficient_stock(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=5,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    with raises(ValueError, match="Insufficient stock"):
        service.remove_stock(
            product_id=product.id,
            quantity=6,
        )

    assert product.quantity == 5


def test_add_stock_rejects_non_positive_quantity(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    with raises(ValueError, match="Quantity must be greater than 0"):
        service.add_stock(
            product_id=product.id,
            quantity=0,
        )

    with raises(ValueError, match="Quantity must be greater than 0"):
        service.add_stock(
            product_id=product.id,
            quantity=-5,
        )

    assert product.quantity == 10


def test_remove_stock_rejects_non_positive_quantity(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(
        name="Electronics",
    )

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=user.id,
            category_id=category.id,
        )
    )

    with raises(ValueError, match="Quantity must be greater than 0"):
        service.remove_stock(
            product_id=product.id,
            quantity=0,
        )

    with raises(ValueError, match="Quantity must be greater than 0"):
        service.remove_stock(
            product_id=product.id,
            quantity=-5,
        )

    assert product.quantity == 10


def test_add_stock_returns_none_when_product_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)

    result = service.add_stock(
        product_id=999,
        quantity=5,
    )

    assert result is None


def test_remove_stock_returns_none_when_product_not_found(
    db_session: Session,
) -> None:
    service = ProductService(db_session)

    result = service.remove_stock(
        product_id=999,
        quantity=5,
    )

    assert result is None
