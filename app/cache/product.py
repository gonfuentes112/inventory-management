import json

from app.db.redis import redis_client
from app.schemas.product import ProductResponse

CACHE_TTL = 60


def get_cached_product(product_id: int) -> ProductResponse | None:
    cached = redis_client.get(f"product:{product_id}")

    if cached is None:
        return None

    return ProductResponse.model_validate(json.loads(cached))


def cache_product(product: ProductResponse) -> None:
    redis_client.set(
        f"product:{product.id}",
        json.dumps(product.model_dump(mode="json")),
        ex=CACHE_TTL,
    )


def delete_cached_product(product_id: int) -> None:
    redis_client.delete(f"product:{product_id}")
