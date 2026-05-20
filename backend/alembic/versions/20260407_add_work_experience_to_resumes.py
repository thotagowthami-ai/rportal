"""add_work_experience_to_resumes

Revision ID: 20260407_add_work_exp
Revises: 15204e33400c
Create Date: 2026-04-07 17:21:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260407_add_work_exp'
down_revision = '15204e33400c'

branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add work_experience column to resumes table
    op.add_column(
        'resumes',
        sa.Column('work_experience', sa.Text(), nullable=True, server_default='[]')
    )


def downgrade() -> None:
    # Remove work_experience column from resumes table
    op.drop_column('resumes', 'work_experience')
