"""Add source fields and status to vocabulary tables

Revision ID: 20250210_add_vocab_source_fields
Revises: 20251211_merge_heads
Create Date: 2025-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250210_add_vocab_source_fields"
down_revision = "20251211_merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("vocabulary_words") as batch:
        batch.add_column(sa.Column("status", sa.String(), nullable=True, server_default="new"))
        batch.add_column(sa.Column("source_lesson_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("source_block_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("user_dictionary") as batch:
        batch.add_column(sa.Column("source_lesson_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("source_block_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("status", sa.String(), nullable=True, server_default="new"))


def downgrade():
    with op.batch_alter_table("user_dictionary") as batch:
        batch.drop_column("status")
        batch.drop_column("source_block_id")
        batch.drop_column("source_lesson_id")
    with op.batch_alter_table("vocabulary_words") as batch:
        batch.drop_column("source_block_id")
        batch.drop_column("source_lesson_id")
        batch.drop_column("status")
