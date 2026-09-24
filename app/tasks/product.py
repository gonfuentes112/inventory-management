import logging

logger = logging.getLogger(__name__)


def log_product_created(product_id: int) -> None:
    logger.info(
        "Product created: product_id=%s",
        product_id,
    )
