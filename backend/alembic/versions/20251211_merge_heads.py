"""Merge multiple heads into a single lineage

This merge unifies:
- 0005_add_answers_to_placement  
- 64e84d938c97_add_vocabulary_and_word_of_week
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = "20251211_merge_heads"
down_revision = (
    "0005_add_answers_to_placement",
    "64e84d938c97",
)
branch_labels = None
depends_on = None


def upgrade():
    # Merge point, no schema changes required.
    pass


def downgrade():
    # Downgrade would need manual branch selection; keep empty for safety.
    pass
