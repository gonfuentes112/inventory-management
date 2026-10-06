from tests.conftest import ProductTestData
import json
import pytest
from decimal import Decimal
from app.core.security import hash_password

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product import ProductService

from app.db.redis import redis_client

from unittest.mock import patch


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

    product = service.create_product(data=data, current_user_id=user.id)

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

    created_product = service.create_product(data=data, current_user_id=user.id)

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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    service.create_product(
        ProductCreate(
            name="Keyboard",
            description="Mechanical keyboard",
            price=100.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    updated_product = service.update_product(
        product_id=product.id,
        data=ProductUpdate(
            name="Gaming Laptop",
            description="High-performance laptop",
            price=1800.00,
            category_id=category.id,
        ),
        current_user_id=user.id,
        is_admin=user.role == "admin",
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
    test_data: ProductTestData,
) -> None:
    service = ProductService(db_session)

    result = service.update_product(
        product_id=999,
        data=ProductUpdate(
            name="Updated Product",
        ),
        current_user_id=test_data["user"].id,
        is_admin=test_data["user"].role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
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

    assert data.category_id == 999

    with pytest.raises(ValueError, match="Category not found"):
        service.create_product(data=data, current_user_id=user.id)


def test_update_product_fails_when_category_not_found(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=test_data["category"].id,
        ),
        current_user_id=test_data["user"].id,
    )

    with pytest.raises(ValueError, match="Category not found"):
        service.update_product(
            product.id,
            ProductUpdate(category_id=999),
            current_user_id=test_data["user"].id,
            is_admin=test_data["user"].role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    updated_product = service.add_stock(
        product_id=product.id,
        quantity=5,
        current_user_id=user.id,
        is_admin=user.role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    updated_product = service.remove_stock(
        product_id=product.id,
        quantity=3,
        current_user_id=user.id,
        is_admin=user.role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    with pytest.raises(ValueError, match="Insufficient stock"):
        service.remove_stock(
            product_id=product.id,
            quantity=6,
            current_user_id=user.id,
            is_admin=user.role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        service.add_stock(
            product_id=product.id,
            quantity=0,
            current_user_id=user.id,
            is_admin=user.role == "admin",
        )

    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        service.add_stock(
            product_id=product.id,
            quantity=-5,
            current_user_id=user.id,
            is_admin=user.role == "admin",
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
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        service.remove_stock(
            product_id=product.id,
            quantity=0,
            current_user_id=user.id,
            is_admin=user.role == "admin",
        )

    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        service.remove_stock(
            product_id=product.id,
            quantity=-5,
            current_user_id=user.id,
            is_admin=user.role == "admin",
        )

    assert product.quantity == 10


def test_add_stock_returns_none_when_product_not_found(
    db_session: Session, test_data: ProductTestData
) -> None:
    service = ProductService(db_session)
    user: User = test_data["user"]
    result = service.add_stock(
        product_id=999,
        quantity=5,
        current_user_id=user.id,
        is_admin=user.role == "admin",
    )

    assert result is None


def test_remove_stock_returns_none_when_product_not_found(
    db_session: Session, test_data: ProductTestData
) -> None:
    service = ProductService(db_session)

    user: User = test_data["user"]

    result = service.remove_stock(
        product_id=999,
        quantity=5,
        current_user_id=user.id,
        is_admin=user.role == "admin",
    )

    assert result is None


def test_get_product_caches_result(db_session: Session) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(name="Electronics")

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    assert redis_client.get(f"product:{product.id}") is None

    service.get_product(product.id)

    cached = redis_client.get(f"product:{product.id}")

    assert cached is not None
    data = json.loads(cached)
    assert data["name"] == "Laptop"


def test_get_product_uses_cache(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(name="Electronics")

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    service.get_product(product.id)

    def fail_if_database_is_called(product_id: int):
        raise AssertionError("PostgreSQL should not be queried")

    service.repository.get_by_id = fail_if_database_is_called

    cached_product = service.get_product(product.id)

    assert cached_product is not None
    assert cached_product.id == product.id
    assert cached_product.name == "Laptop"


def test_update_product_invalidates_cache(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(name="Electronics")

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    service.get_product(product.id)

    assert redis_client.get(f"product:{product.id}") is not None

    service.update_product(
        product.id,
        ProductUpdate(name="Gaming Laptop"),
        current_user_id=user.id,
        is_admin=user.role == "admin",
    )

    assert redis_client.get(f"product:{product.id}") is None


def test_add_stock_invalidates_cache(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(name="Electronics")

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    service.get_product(product.id)

    assert redis_client.get(f"product:{product.id}") is not None

    service.add_stock(
        product_id=product.id,
        quantity=5,
        current_user_id=user.id,
        is_admin=user.role == "admin",
    )

    assert redis_client.get(f"product:{product.id}") is None


def test_remove_stock_invalidates_cache(
    db_session: Session,
) -> None:
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword123",
    )

    category = Category(name="Electronics")

    db_session.add_all([user, category])
    db_session.commit()

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=user.id,
    )

    service.get_product(product.id)

    assert redis_client.get(f"product:{product.id}") is not None

    service.remove_stock(
        product.id,
        3,
        current_user_id=user.id,
        is_admin=user.role == "admin",
    )

    assert redis_client.get(f"product:{product.id}") is None


def test_get_product_returns_cached_product(
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
            category_id=test_data["category"].id,
        ),
        current_user_id=test_data["user"].id,
    )

    with patch("app.services.product.get_cached_product") as mock_get_cached:
        mock_get_cached.return_value = product

        result = service.get_product(product.id)

    assert result is not None
    assert result.id == product.id
    assert result.name == "Laptop"

    mock_get_cached.assert_called_once_with(product.id)


def test_get_product_queries_database_on_cache_miss(
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
            category_id=test_data["category"].id,
        ),
        current_user_id=test_data["user"].id,
    )

    with (
        patch(
            "app.services.product.get_cached_product",
            return_value=None,
        ),
        patch.object(
            service.repository,
            "get_by_id",
            wraps=service.repository.get_by_id,
        ) as mock_get_by_id,
    ):
        result = service.get_product(product.id)

    assert result is not None
    assert result.id == product.id

    mock_get_by_id.assert_called_once_with(product.id)


def test_non_owner_cannot_update_product(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    owner = test_data["user"]
    category = test_data["category"]

    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=hash_password("otherpassword123"),
        role="user",
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=Decimal("1200.00"),
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=owner.id,
    )

    with pytest.raises(PermissionError, match="Not authorized"):
        service.update_product(
            product.id,
            ProductUpdate(name="Hacked Laptop"),
            current_user_id=other_user.id,
            is_admin=False,
        )


def test_admin_can_update_product(
    db_session: Session,
    test_data: ProductTestData,
) -> None:
    owner = test_data["user"]
    category = test_data["category"]

    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        role="admin",
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    service = ProductService(db_session)

    product = service.create_product(
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=Decimal("1200.00"),
            quantity=10,
            category_id=category.id,
        ),
        current_user_id=owner.id,
    )

    updated_product = service.update_product(
        product.id,
        ProductUpdate(name="Admin Updated Laptop"),
        current_user_id=admin.id,
        is_admin=True,
    )

    assert updated_product is not None
    assert updated_product.name == "Admin Updated Laptop"
    assert updated_product.owner_id == owner.id
