"""merge multiple heads

Revision ID: 15204e33400c
Revises: 8b7c0d250aac, 9f3b2c4d1e9a
Create Date: 2026-02-20 16:15:59.291954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15204e33400c'
down_revision: Union[str, None] = ('8b7c0d250aac', '9f3b2c4d1e9a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
