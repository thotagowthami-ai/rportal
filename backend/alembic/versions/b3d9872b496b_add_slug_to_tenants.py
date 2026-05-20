"""add_slug_to_tenants

Revision ID: b3d9872b496b
Revises: 551bdcabfc34
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3d9872b496b'
down_revision = '551bdcabfc34'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add slug column
    op.add_column('tenants', sa.Column('slug', sa.String(100), nullable=True))
    
    # Generate slugs for existing tenants (lowercase name with hyphens)
    op.execute("""
        UPDATE tenants 
        SET slug = LOWER(REPLACE(name, ' ', '-'))
        WHERE slug IS NULL
    """)
    
    # Make slug NOT NULL and UNIQUE
    op.alter_column('tenants', 'slug', nullable=False)
    op.create_unique_constraint('uq_tenants_slug', 'tenants', ['slug'])
    
    # Create index on slug
    op.create_index('idx_tenants_slug', 'tenants', ['slug'])

def downgrade() -> None:
    op.drop_index('idx_tenants_slug', table_name='tenants')
    op.drop_constraint('uq_tenants_slug', 'tenants', type_='unique')
    op.drop_column('tenants', 'slug')
