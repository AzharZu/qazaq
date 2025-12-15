"""Add audio_tasks and pronunciation_blocks tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = "20251221_add_audio_and_pronunciation_tables"
down_revision = "20251220_add_level_test_and_progress_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Create audio_tasks table
    op.create_table(
        "audio_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("transcript", sa.String(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.String(), nullable=True),
        sa.Column("answer_type", sa.String(), nullable=False, server_default="text"),
        sa.Column("feedback", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(["block_id"], ["lesson_blocks.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("block_id"),
    )
    op.create_index(op.f("ix_audio_tasks_block_id"), "audio_tasks", ["block_id"], unique=True)

    # Create pronunciation_blocks table
    op.create_table(
        "pronunciation_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=False),
        sa.Column("reference_audio_url", sa.String(), nullable=True),
        sa.Column("reference_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(["block_id"], ["lesson_blocks.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("block_id"),
    )
    op.create_index(op.f("ix_pronunciation_blocks_block_id"), "pronunciation_blocks", ["block_id"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_pronunciation_blocks_block_id"), table_name="pronunciation_blocks")
    op.drop_table("pronunciation_blocks")
    op.drop_index(op.f("ix_audio_tasks_block_id"), table_name="audio_tasks")
    op.drop_table("audio_tasks")
