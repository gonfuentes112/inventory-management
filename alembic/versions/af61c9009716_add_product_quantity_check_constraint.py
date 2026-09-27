"""add product quantity check constraint

Revision ID: af61c9009716
Revises: 675d413f16dd
Create Date: 2026-09-28 00:53:07.653776

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af61c9009716"
down_revision: Union[str, Sequence[str], None] = "675d413f16dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_products_quantity_non_negative",
        "products",
        "quantity >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_products_quantity_non_negative",
        "products",
        type_="check",
    )
