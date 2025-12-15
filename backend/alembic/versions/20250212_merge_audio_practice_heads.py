"""Merge heads: last_practiced + audio/pronunciation tables"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20250212_merge_audio_practice_heads"
down_revision = ("20250211_add_last_practiced", "20251221_add_audio_and_pronunciation_tables")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
