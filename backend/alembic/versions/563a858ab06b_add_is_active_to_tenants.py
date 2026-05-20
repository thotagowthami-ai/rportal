"""add_is_active_to_tenants

Revision ID: 563a858ab06b
Revises: b3d9872b496b
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '563a858ab06b'
down_revision = 'b3d9872b496b'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add is_active column
    op.add_column('tenants', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    
    # Update existing tenants
    op.execute("UPDATE tenants SET is_active = true WHERE is_active IS NULL")
    
    # Make is_active NOT NULL
    op.alter_column('tenants', 'is_active', nullable=False)

def downgrade() -> None:
    op.drop_column('tenants', 'is_active')
