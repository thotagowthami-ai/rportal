"""add_rls_policies_fail_closed

🔴 CRITICAL SECURITY UPDATE (v3.1)
- Implements fail-closed Row-Level Security policies
- Prevents cross-tenant data leakage at database level
- Enforces automatic tenant filtering on all queries

⚠️ BREAKING CHANGE: After this migration, all queries on tenant-scoped
tables MUST set tenant context via set_tenant_context() or will return zero rows.

Revision ID: c4fc24be56e9
Revises: c2c8f4bc82b7
Create Date: 2026-02-04 00:54:46.756607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4fc24be56e9'
down_revision: Union[str, None] = 'c2c8f4bc82b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable Row-Level Security (RLS) with fail-closed enforcement.
    
    Security Model:
    1. Create current_tenant_id() function that reads session variable
    2. Enable RLS on all tenant-scoped tables
    3. Create policies that filter by tenant_id = current_tenant_id()
    4. If current_tenant_id() returns NULL → policy denies access (fail-closed)
    
    This prevents accidental data leakage from missing tenant context.
    """
    
    # ========================================================================
    # Step 1: Create helper function for RLS policies
    # ========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION current_tenant_id()
        RETURNS UUID AS $$
        BEGIN
            -- Read session variable, return NULL if not set
            -- NULL causes RLS policies to deny access (fail-closed)
            RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
    """)
    
    op.execute("""
        COMMENT ON FUNCTION current_tenant_id() IS 
        'Returns current tenant UUID from session variable. Returns NULL if not set, causing RLS policies to fail-closed.';
    """)
    
    # ========================================================================
    # Step 2: Enable RLS on users table
    # ========================================================================
    # Note: Tenants table does NOT have RLS since it's not tenant-scoped
    # (tenants can see their own tenant record via tenant_id FK)
    
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    
    # ========================================================================
    # Step 3: Create RLS policy for users table
    # ========================================================================
    # Policy: Users can only see other users in the same tenant
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON users
        FOR ALL
        USING (tenant_id = current_tenant_id());
    """)
    
    op.execute("""
        COMMENT ON POLICY tenant_isolation_policy ON users IS 
        'Fail-closed RLS: Returns zero rows if current_tenant_id() is NULL. Filters all queries to current tenant only.';
    """)
    
    # ========================================================================
    # Step 4: Create composite indexes for performance with RLS
    # ========================================================================
    # v3.1 ENHANCEMENT: Indexes that include tenant_id for efficient filtering
    # This prevents RLS from degrading query performance
    
    op.create_index(
        'idx_users_tenant_email',
        'users',
        ['tenant_id', 'email'],
        unique=False
    )
    
    op.create_index(
        'idx_users_tenant_active',
        'users',
        ['tenant_id', 'is_active'],
        unique=False
    )


def downgrade() -> None:
    """
    Remove RLS policies and helper functions.
    
    ⚠️ WARNING: Downgrading removes tenant isolation at database level!
    Only do this in development environments.
    """
    
    # Drop indexes
    op.drop_index('idx_users_tenant_active', table_name='users')
    op.drop_index('idx_users_tenant_email', table_name='users')
    
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON users;")
    
    # Disable RLS
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    
    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS current_tenant_id();")
    
    print("⚠️  RLS policies removed - tenant isolation is NO LONGER ENFORCED at database level!")
