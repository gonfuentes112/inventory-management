from unittest.mock import patch

from app.tasks.product import log_product_created


def test_log_product_created() -> None:
    with patch("app.tasks.product.logger") as mock_logger:
        log_product_created(123)

        mock_logger.info.assert_called_once_with(
            "Product created: product_id=%s",
            123,
        )
