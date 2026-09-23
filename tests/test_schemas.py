from pydantic import ValidationError
import pytest

from app.schemas.product import ProductCreate


def test_product_create_schema():
    product = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=1,
        category_id=1,
    )

    assert product.name == "Laptop"
    assert product.price == 1200.00


def test_product_create_rejects_negative_price():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Laptop",
            description="Development laptop",
            price=-100,
            quantity=10,
            owner_id=1,
            category_id=1,
        )


def test_product_create_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="",
            description="Development laptop",
            price=1200.00,
            quantity=10,
            owner_id=1,
            category_id=1,
        )


from app.models.product import Product
from app.schemas.product import ProductResponse


def test_product_response_from_orm():
    product = Product(
        id=1,
        name="Laptop",
        description="Development laptop",
        price=1200.00,
        quantity=10,
        owner_id=1,
        category_id=1,
    )

    response = ProductResponse.model_validate(product)

    assert response.id == 1
    assert response.name == "Laptop"
    assert response.description == "Development laptop"
    assert response.price == 1200.00
    assert response.owner_id == 1
    assert response.category_id == 1


from app.services.product import ProductUpdate


def test_product_update_schema():
    product = ProductUpdate(
        price=999.99,
    )

    assert product.name is None
    assert product.description is None
    assert product.price == 999.99
    assert product.category_id is None


def test_product_update_rejects_negative_price():
    with pytest.raises(ValidationError):
        ProductUpdate(
            price=-100,
        )
