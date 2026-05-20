"""add_role_column_to_users

Revision ID: 72b8aeed3146
Revises: abc123
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '72b8aeed3146'
down_revision = 'abc123'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add role column to users table
    op.add_column('users', sa.Column('role', sa.String(50), nullable=True, server_default='recruiter'))
    
    # Update existing users to have 'recruiter' role
    op.execute("UPDATE users SET role = 'recruiter' WHERE role IS NULL")
    
    # Make role NOT NULL after setting defaults
    op.alter_column('users', 'role', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'role')
