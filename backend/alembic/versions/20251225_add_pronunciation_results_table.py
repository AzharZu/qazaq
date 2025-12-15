"""Add pronunciation_results table for dictionary progress tracking"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = "20251225_add_pronunciation_results_table"
down_revision = "20250212_merge_audio_practice_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pronunciation_results",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("word_id", sa.Integer(), sa.ForeignKey("vocabulary_words.id"), nullable=False),
        sa.Column("audio_url", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=func.now()),
    )
    op.create_index(op.f("ix_pronunciation_results_user_id"), "pronunciation_results", ["user_id"], unique=False)
    op.create_index(op.f("ix_pronunciation_results_word_id"), "pronunciation_results", ["word_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_pronunciation_results_word_id"), table_name="pronunciation_results")
    op.drop_index(op.f("ix_pronunciation_results_user_id"), table_name="pronunciation_results")
    op.drop_table("pronunciation_results")
