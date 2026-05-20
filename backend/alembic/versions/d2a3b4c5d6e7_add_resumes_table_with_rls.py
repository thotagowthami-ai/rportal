"""add_resumes_table_with_rls

Revision ID: d2a3b4c5d6e7
Revises: c4fc24be56e9
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'd2a3b4c5d6e7'
down_revision = 'da1ee848a7d8'

branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension FIRST
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_name', sa.String(255), nullable=False),
        sa.Column('candidate_email', sa.String(255), nullable=True),
        sa.Column('candidate_phone', sa.String(50), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('current_role', sa.String(255), nullable=True),
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
    )

    # Indexes - FIXED: separate tenant and embedding indexes
    op.create_index('idx_resumes_tenant', 'resumes', ['tenant_id'])
    op.create_index('idx_resumes_uploaded_by', 'resumes', ['uploaded_by'])
    op.create_index('idx_resumes_candidate_email', 'resumes', ['candidate_email'])
    
    # IVFFlat index for vector similarity (single column only)
    op.create_index(
        'idx_resumes_embedding', 
        'resumes', 
        ['embedding'], 
        postgresql_using='ivfflat',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
        postgresql_with={'lists': 100}
    )

    # Enable RLS
    op.execute("ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON resumes
        USING (tenant_id = current_tenant_id());
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON resumes;")
    op.execute("ALTER TABLE resumes DISABLE ROW LEVEL SECURITY;")

    op.drop_index('idx_resumes_embedding', table_name='resumes')
    op.drop_index('idx_resumes_candidate_email', table_name='resumes')
    op.drop_index('idx_resumes_uploaded_by', table_name='resumes')
    op.drop_index('idx_resumes_tenant', table_name='resumes')

    op.drop_table('resumes')
    op.execute('DROP EXTENSION IF EXISTS vector')
