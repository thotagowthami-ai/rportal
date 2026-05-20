"""add_rls_to_job_descriptions

Revision ID: 8b7c0d250aac
"""
from alembic import op

# revision identifiers
revision = '8b7c0d250aac'
down_revision = None  # Update this to your previous migration ID if you have one
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on job_descriptions table"""
    
    # Enable RLS on job_descriptions table
    op.execute("""
        ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;
    """)
    
    # Make migration idempotent when policy was already created manually
    # or by an earlier migration run.
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON job_descriptions;")

    # v3.1 CHANGE: NO bypass_rls_policy - System now fails-closed
    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON job_descriptions
        USING (tenant_id = current_tenant_id());
    """)


def downgrade() -> None:
    """Disable RLS on job_descriptions table"""
    
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON job_descriptions;")
    op.execute("ALTER TABLE job_descriptions DISABLE ROW LEVEL SECURITY;")
