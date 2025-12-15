"""add answers json to placement_results"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_add_answers_to_placement"
down_revision = "20251201_add_lesson_progress_table"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("placement_results", sa.Column("answers", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("placement_results", "answers")
