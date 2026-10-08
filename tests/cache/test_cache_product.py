import json
from decimal import Decimal

from app.cache.product import (
    cache_product,
    delete_cached_product,
    get_cached_product,
)
from app.schemas.product import ProductResponse


def create_product_response() -> ProductResponse:
    return ProductResponse(
        id=1,
        name="Test Product",
        description="Test description",
        price=Decimal("100.00"),
        quantity=10,
        owner_id=1,
        category_id=1,
    )


def test_get_cached_product_returns_none_on_cache_miss(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.cache.product.redis_client.get",
        lambda key: None,
    )

    result = get_cached_product(1)

    assert result is None


def test_get_cached_product_returns_cached_product(
    monkeypatch,
) -> None:
    product = create_product_response()

    monkeypatch.setattr(
        "app.cache.product.redis_client.get",
        lambda key: json.dumps(product.model_dump(mode="json")),
    )

    result = get_cached_product(product.id)

    assert result is not None
    assert result.id == product.id
    assert result.name == product.name
    assert result.price == product.price
    assert result.quantity == product.quantity


def test_get_cached_product_handles_redis_failure(
    monkeypatch,
) -> None:
    def raise_redis_error(key):
        from redis.exceptions import RedisError

        raise RedisError("Redis unavailable")

    monkeypatch.setattr(
        "app.cache.product.redis_client.get",
        raise_redis_error,
    )

    result = get_cached_product(1)

    assert result is None


def test_get_cached_product_handles_invalid_cached_data(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.cache.product.redis_client.get",
        lambda key: "not valid json",
    )

    result = get_cached_product(1)

    assert result is None


def test_cache_product_handles_redis_failure(
    monkeypatch,
) -> None:
    def raise_redis_error(*args, **kwargs):
        from redis.exceptions import RedisError

        raise RedisError("Redis unavailable")

    monkeypatch.setattr(
        "app.cache.product.redis_client.set",
        raise_redis_error,
    )

    product = create_product_response()

    cache_product(product)


def test_delete_cached_product_handles_redis_failure(
    monkeypatch,
) -> None:
    def raise_redis_error(*args, **kwargs):
        from redis.exceptions import RedisError

        raise RedisError("Redis unavailable")

    monkeypatch.setattr(
        "app.cache.product.redis_client.delete",
        raise_redis_error,
    )

    delete_cached_product(1)
