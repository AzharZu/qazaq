"""Add missing columns to user_progress (time_spent, completed_at)"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251216_add_user_progress_columns"
down_revision = "20251215_fix_lesson_block_defaults"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_progress", sa.Column("time_spent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_progress", sa.Column("completed_at", sa.DateTime(), nullable=True))
    with op.batch_alter_table("user_progress") as batch:
        batch.alter_column("time_spent", server_default=None)


def downgrade():
    with op.batch_alter_table("user_progress") as batch:
        batch.drop_column("completed_at")
        batch.drop_column("time_spent")
