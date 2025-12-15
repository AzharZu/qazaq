"""Add last_practiced_at to vocabulary tables

Revision ID: 20250211_add_last_practiced
Revises: 20250210_add_vocab_source_fields
Create Date: 2025-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250211_add_last_practiced"
down_revision = "20250210_add_vocab_source_fields"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("vocabulary_words") as batch:
        batch.add_column(sa.Column("last_practiced_at", sa.DateTime(), nullable=True))
    with op.batch_alter_table("user_dictionary") as batch:
        batch.add_column(sa.Column("last_practiced_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("user_dictionary") as batch:
        batch.drop_column("last_practiced_at")
    with op.batch_alter_table("vocabulary_words") as batch:
        batch.drop_column("last_practiced_at")
