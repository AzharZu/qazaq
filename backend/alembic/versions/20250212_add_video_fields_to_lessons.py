"""Add video fields to lessons

Revision ID: 20250212_add_video_fields_to_lessons
Revises: 20250211_add_last_practiced
Create Date: 2025-02-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250212_add_video_fields_to_lessons"
down_revision = "20250211_add_last_practiced"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {col["name"] for col in insp.get_columns("lessons")}
    with op.batch_alter_table("lessons") as batch:
        if "video_type" not in existing:
            batch.add_column(sa.Column("video_type", sa.String(), nullable=True))
        if "video_url" not in existing:
            batch.add_column(sa.Column("video_url", sa.String(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {col["name"] for col in insp.get_columns("lessons")}
    with op.batch_alter_table("lessons") as batch:
        if "video_url" in existing:
            batch.drop_column("video_url")
        if "video_type" in existing:
            batch.drop_column("video_type")
