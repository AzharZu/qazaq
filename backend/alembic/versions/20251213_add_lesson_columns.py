"""Add missing lesson columns (status, language, version, blocks_order, soft-delete, timestamps)"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251213_add_lesson_columns"
down_revision = "20251212_fix_admin_hash"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    op.add_column("lessons", sa.Column("status", sa.String(), nullable=False, server_default="draft"))
    op.add_column("lessons", sa.Column("language", sa.String(), nullable=False, server_default="kk"))
    op.add_column("lessons", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("lessons", sa.Column("blocks_order", sa.JSON(), nullable=True))
    op.add_column("lessons", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("lessons", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column(
        "lessons",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=None if is_sqlite else sa.func.now(),
            nullable=True if is_sqlite else False,
        ),
    )
    op.add_column(
        "lessons",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=None if is_sqlite else sa.func.now(),
            onupdate=None if is_sqlite else sa.func.now(),
            nullable=True if is_sqlite else False,
        ),
    )
    if is_sqlite:
        # SQLite cannot add non-constant defaults; backfill timestamps for existing rows.
        bind.execute(sa.text("UPDATE lessons SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    # drop server defaults to keep app-level defaults after existing rows are populated
    with op.batch_alter_table("lessons") as batch:
        batch.alter_column("status", server_default=None)
        batch.alter_column("language", server_default=None)
        batch.alter_column("version", server_default=None)
        batch.alter_column("is_deleted", server_default=None)
        batch.alter_column("created_at", server_default=None)
        batch.alter_column("updated_at", server_default=None)


def downgrade():
    with op.batch_alter_table("lessons") as batch:
        batch.drop_column("updated_at")
        batch.drop_column("created_at")
        batch.drop_column("deleted_at")
        batch.drop_column("is_deleted")
        batch.drop_column("blocks_order")
        batch.drop_column("version")
        batch.drop_column("language")
        batch.drop_column("status")
