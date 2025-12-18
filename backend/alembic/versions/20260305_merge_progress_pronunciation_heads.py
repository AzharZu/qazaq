"""Merge progress and pronunciation heads into single lineage."""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260305_merge_progress_pronunciation_heads"
down_revision = ("20260303_add_user_stats_table", "20251225_add_pronunciation_results_table")
branch_labels = None
depends_on = None


def upgrade():
    # Merge point; no schema changes.
    pass


def downgrade():
    # To downgrade, choose the branch you need manually.
    pass
