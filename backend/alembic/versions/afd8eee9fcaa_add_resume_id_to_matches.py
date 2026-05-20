from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "afd8eee9fcaa"
down_revision = "563a858ab06b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE matches ADD COLUMN IF NOT EXISTS resume_id UUID;")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_matches_resume_id'
            ) THEN
                ALTER TABLE matches
                ADD CONSTRAINT fk_matches_resume_id
                FOREIGN KEY (resume_id)
                REFERENCES resumes(id)
                ON DELETE CASCADE;
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE matches DROP CONSTRAINT IF EXISTS matches_candidate_id_fkey;")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS candidate_id;")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_match_unique ON matches (job_description_id, resume_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_match_unique;")
    op.execute("ALTER TABLE matches DROP CONSTRAINT IF EXISTS fk_matches_resume_id;")
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS resume_id;")
    op.execute("ALTER TABLE matches ADD COLUMN IF NOT EXISTS candidate_id UUID;")
