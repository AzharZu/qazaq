"""add audio_path columns for flashcards and audio tasks

Revision ID: 20250213_add_audio_path_fields
Revises: 20250212_add_video_fields_to_lessons
Create Date: 2025-02-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250213_add_audio_path_fields"
down_revision = "20250212_add_video_fields_to_lessons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("flashcards") as batch:
        batch.add_column(sa.Column("audio_path", sa.String(), nullable=True))
    with op.batch_alter_table("audio_tasks") as batch:
        batch.add_column(sa.Column("audio_path", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("audio_tasks") as batch:
        batch.drop_column("audio_path")
    with op.batch_alter_table("flashcards") as batch:
        batch.drop_column("audio_path")
