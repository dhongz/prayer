"""add_provider_id_user

Revision ID: 0c968e822101
Revises: 956438a471a7
Create Date: 2025-02-20 06:39:00.604228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c968e822101'
down_revision: Union[str, None] = '956438a471a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
