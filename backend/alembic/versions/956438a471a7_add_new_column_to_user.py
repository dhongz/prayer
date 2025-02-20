"""add_new_column_to_user

Revision ID: 956438a471a7
Revises: b9a0af5cf309
Create Date: 2025-02-20 01:35:58.193344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '956438a471a7'
down_revision: Union[str, None] = 'b9a0af5cf309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
