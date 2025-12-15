"""Add soft-delete and timestamps to lesson_blocks"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251214_add_lesson_block_columns"
down_revision = "20251214_add_data_to_lesson_blocks"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    op.add_column("lesson_blocks", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("lesson_blocks", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column(
        "lesson_blocks",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=None if is_sqlite else sa.func.now(),
            nullable=True if is_sqlite else False,
        ),
    )
    op.add_column(
        "lesson_blocks",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=None if is_sqlite else sa.func.now(),
            onupdate=None if is_sqlite else sa.func.now(),
            nullable=True if is_sqlite else False,
        ),
    )
    if is_sqlite:
        bind.execute(sa.text("UPDATE lesson_blocks SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    with op.batch_alter_table("lesson_blocks") as batch:
        batch.alter_column("is_deleted", server_default=None)
        batch.alter_column("created_at", server_default=None)
        batch.alter_column("updated_at", server_default=None)


def downgrade():
    with op.batch_alter_table("lesson_blocks") as batch:
        batch.drop_column("updated_at")
        batch.drop_column("created_at")
        batch.drop_column("deleted_at")
        batch.drop_column("is_deleted")
