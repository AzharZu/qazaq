"""Add data column to lesson_blocks"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251214_add_data_to_lesson_blocks"
down_revision = "20251213_add_lesson_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "lesson_blocks",
        sa.Column("data", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("lesson_blocks", "data")
