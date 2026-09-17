from pydantic import ValidationError
import pytest

from app.schemas.product import ProductCreate


def test_product_create_schema():
    product = ProductCreate(
        name="Laptop",
        description="Development laptop",
        price=1200.00,
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
            owner_id=1,
            category_id=1,
        )


def test_product_create_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="",
            description="Development laptop",
            price=1200.00,
            owner_id=1,
            category_id=1,
        )
