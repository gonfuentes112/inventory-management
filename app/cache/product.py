import json

from redis.exceptions import RedisError

from app.db.redis import redis_client
from app.schemas.product import ProductResponse

CACHE_TTL = 60


def get_cached_product(product_id: int) -> ProductResponse | None:
    try:
        cached = redis_client.get(f"product:{product_id}")
    except RedisError:
        return None

    if cached is None:
        return None

    try:
        return ProductResponse.model_validate(json.loads(cached))
    except (json.JSONDecodeError, ValueError):
        return None


def cache_product(product: ProductResponse) -> None:
    try:
        redis_client.set(
            f"product:{product.id}",
            json.dumps(product.model_dump(mode="json")),
            ex=CACHE_TTL,
        )
    except RedisError:
        pass


def delete_cached_product(product_id: int) -> None:
    try:
        redis_client.delete(f"product:{product_id}")
    except RedisError:
        pass
