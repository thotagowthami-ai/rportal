"""add_matches_table_with_rls

Revision ID: abc123
Revises: 7c22d6a90ee6
Create Date: 2026-02-05 14:15:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "abc123"
down_revision = "7c22d6a90ee6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE matchstatus AS ENUM (
                'NEW', 'REVIEWED', 'SHORTLISTED',
                'REJECTED', 'INTERVIEWED', 'OFFERED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("skill_match_score", sa.Float(), nullable=True),
        sa.Column("experience_match_score", sa.Float(), nullable=True),
        sa.Column("education_match_score", sa.Float(), nullable=True),
        sa.Column("matched_skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("missing_skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("match_reasoning", sa.Text(), nullable=True),
        sa.Column(
            "recruiter_status",
            postgresql.ENUM(
                "NEW",
                "REVIEWED",
                "SHORTLISTED",
                "REJECTED",
                "INTERVIEWED",
                "OFFERED",
                name="matchstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="NEW",
        ),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_match_job_score_desc", "matches", ["job_description_id", "overall_score"], unique=False)
    op.create_index("idx_match_job_status", "matches", ["job_description_id", "recruiter_status"], unique=False)
    op.create_index("idx_match_tenant_status", "matches", ["tenant_id", "recruiter_status"], unique=False)
    op.create_index("idx_match_unique", "matches", ["job_description_id", "resume_id"], unique=True)
    op.create_index("ix_matches_created_at", "matches", ["created_at"], unique=False)
    op.create_index("ix_matches_id", "matches", ["id"], unique=False)
    op.create_index("ix_matches_overall_score", "matches", ["overall_score"], unique=False)
    op.create_index("ix_matches_recruiter_status", "matches", ["recruiter_status"], unique=False)
    op.create_index("ix_matches_tenant_id", "matches", ["tenant_id"], unique=False)
    op.create_index("ix_matches_job_description_id", "matches", ["job_description_id"], unique=False)
    op.create_index("ix_matches_resume_id", "matches", ["resume_id"], unique=False)

    # Enable RLS
    op.execute("ALTER TABLE matches ENABLE ROW LEVEL SECURITY;")

    # Create RLS policy
    op.execute(
        """
        CREATE POLICY tenant_isolation_policy ON matches
        USING (tenant_id = current_tenant_id());
        """
    )


def downgrade() -> None:
    # Drop RLS
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON matches;")
    op.execute("ALTER TABLE matches DISABLE ROW LEVEL SECURITY;")

    # Drop indexes
    op.drop_index("ix_matches_resume_id", table_name="matches")
    op.drop_index("ix_matches_job_description_id", table_name="matches")
    op.drop_index("ix_matches_tenant_id", table_name="matches")
    op.drop_index("ix_matches_recruiter_status", table_name="matches")
    op.drop_index("ix_matches_overall_score", table_name="matches")
    op.drop_index("ix_matches_id", table_name="matches")
    op.drop_index("ix_matches_created_at", table_name="matches")
    op.drop_index("idx_match_unique", table_name="matches")
    op.drop_index("idx_match_tenant_status", table_name="matches")
    op.drop_index("idx_match_job_status", table_name="matches")
    op.drop_index("idx_match_job_score_desc", table_name="matches")

    # Drop table and enum
    op.drop_table("matches")
    op.execute("DROP TYPE IF EXISTS matchstatus;")
