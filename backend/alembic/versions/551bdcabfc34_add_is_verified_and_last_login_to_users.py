"""add_is_verified_and_last_login_to_users

Revision ID: 551bdcabfc34
Revises: 72b8aeed3146
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '551bdcabfc34'
down_revision = '72b8aeed3146'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add is_verified column
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'))
    
    # Add last_login column
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Update existing users
    op.execute("UPDATE users SET is_verified = false WHERE is_verified IS NULL")
    
    # Make is_verified NOT NULL
    op.alter_column('users', 'is_verified', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_verified')
