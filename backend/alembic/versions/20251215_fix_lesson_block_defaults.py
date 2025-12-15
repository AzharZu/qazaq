"""Set server defaults for lesson_blocks timestamps"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = "20251215_fix_lesson_block_defaults"
down_revision = "20251214_add_lesson_block_columns"
branch_labels = None
depends_on = None


def upgrade():
    # Set defaults
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    if not is_sqlite:
        op.alter_column("lesson_blocks", "created_at", server_default=sa.func.now(), existing_nullable=False)
        op.alter_column("lesson_blocks", "updated_at", server_default=sa.func.now(), existing_nullable=False)
        op.execute(sa.text("UPDATE lesson_blocks SET created_at = COALESCE(created_at, NOW()), updated_at = COALESCE(updated_at, NOW())"))
    else:
        # SQLite: keep nullable columns from previous migration, just backfill values.
        op.execute(sa.text("UPDATE lesson_blocks SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP), updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column("lesson_blocks", "updated_at", server_default=None, existing_nullable=False)
        op.alter_column("lesson_blocks", "created_at", server_default=None, existing_nullable=False)
