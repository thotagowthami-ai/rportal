"""add_composite_vector_indexes

Revision ID: 9f3b2c4d1e9a
Revises: afd8eee9fcaa
Create Date: 2026-02-08 14:10:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f3b2c4d1e9a"
down_revision = "afd8eee9fcaa"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- JOB DESCRIPTIONS ---

    # Drop old vector index (if exists)
    op.drop_index("idx_job_descriptions_embedding", table_name="job_descriptions")

    # Add normal btree index for tenant_id
    op.create_index(
        "idx_job_descriptions_tenant_id",
        "job_descriptions",
        ["tenant_id"],
    )

    # Add vector index ONLY on embedding
    op.create_index(
        "idx_job_descriptions_embedding",
        "job_descriptions",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )

    # --- RESUMES ---

    op.drop_index("idx_resumes_embedding", table_name="resumes")

    op.create_index(
        "idx_resumes_tenant_id",
        "resumes",
        ["tenant_id"],
    )

    op.create_index(
        "idx_resumes_embedding",
        "resumes",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )
def downgrade() -> None:
    # --- RESUMES ---
    op.drop_index("idx_resumes_embedding", table_name="resumes")
    op.drop_index("idx_resumes_tenant_id", table_name="resumes")

    op.create_index(
        "idx_resumes_embedding",
        "resumes",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )

    # --- JOB DESCRIPTIONS ---
    op.drop_index("idx_job_descriptions_embedding", table_name="job_descriptions")
    op.drop_index("idx_job_descriptions_tenant_id", table_name="job_descriptions")

    op.create_index(
        "idx_job_descriptions_embedding",
        "job_descriptions",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )
