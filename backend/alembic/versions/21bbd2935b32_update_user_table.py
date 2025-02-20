"""update_user_table

Revision ID: 21bbd2935b32
Revises: 0c968e822101
Create Date: 2025-02-20 06:41:50.043005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21bbd2935b32'
down_revision: Union[str, None] = '0c968e822101'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('provider_id', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'provider_id')
    # ### end Alembic commands ###
