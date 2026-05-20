"""add_candidates_table_with_rls

Revision ID: 7c22d6a90ee6
Revises: d2a3b4c5d6e7
Create Date: 2026-02-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7c22d6a90ee6'
down_revision = 'd2a3b4c5d6e7'

branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('candidate_name', sa.String(255), nullable=False),
        sa.Column('candidate_email', sa.String(255), nullable=True),
        sa.Column('candidate_phone', sa.String(50), nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('current_role', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
    )

    op.create_index('idx_candidates_tenant', 'candidates', ['tenant_id'])
    op.create_index('idx_candidates_email', 'candidates', ['candidate_email'])
    op.create_index('idx_candidates_resume', 'candidates', ['resume_id'])

    op.execute("ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON candidates
        USING (tenant_id = current_tenant_id());
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON candidates;")
    op.execute("ALTER TABLE candidates DISABLE ROW LEVEL SECURITY;")
    op.drop_index('idx_candidates_resume', table_name='candidates')
    op.drop_index('idx_candidates_email', table_name='candidates')
    op.drop_index('idx_candidates_tenant', table_name='candidates')
    op.drop_table('candidates')
