"""add_job_descriptions_table_with_rls

Revision ID: da1ee848a7d8
Revises: c4fc24be56e9
Create Date: 2026-02-06 14:48:42.935225

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'da1ee848a7d8'
down_revision = 'c4fc24be56e9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Enable pgvector extension FIRST
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    op.create_table(
        'job_descriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('required_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_required', sa.Integer(), nullable=True),
        sa.Column('education_required', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('employment_type', sa.String(50), nullable=True),
        sa.Column('salary_range', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )

    op.create_index('idx_job_descriptions_tenant', 'job_descriptions', ['tenant_id'])
    op.create_index('idx_job_descriptions_created_by', 'job_descriptions', ['created_by'])
    op.create_index('idx_job_descriptions_status', 'job_descriptions', ['status'])
    op.create_index(
        'idx_job_descriptions_embedding',
        'job_descriptions',
        ['embedding'],
        postgresql_using='ivfflat',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
        postgresql_with={'lists': 100}
    )

    op.execute("ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON job_descriptions
        USING (tenant_id = current_tenant_id());
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON job_descriptions;")
    op.execute("ALTER TABLE job_descriptions DISABLE ROW LEVEL SECURITY;")
    op.drop_index('idx_job_descriptions_embedding', table_name='job_descriptions')
    op.drop_index('idx_job_descriptions_status', table_name='job_descriptions')
    op.drop_index('idx_job_descriptions_created_by', table_name='job_descriptions')
    op.drop_index('idx_job_descriptions_tenant', table_name='job_descriptions')
    op.drop_table('job_descriptions')
    op.execute('DROP EXTENSION IF EXISTS vector')
