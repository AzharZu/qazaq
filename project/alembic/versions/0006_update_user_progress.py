"""add time_spent completed_at unique to user_progress"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_update_user_progress"
down_revision = "0005_add_answers_to_placement"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    def has_column(table: str, column: str) -> bool:
        res = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
        return any(row[1] == column for row in res)

    if not has_column("user_progress", "time_spent"):
        op.add_column("user_progress", sa.Column("time_spent", sa.Integer(), nullable=False, server_default="0"))
    if not has_column("user_progress", "completed_at"):
        op.add_column("user_progress", sa.Column("completed_at", sa.DateTime(), nullable=True))

    # SQLite doesn't support altering default cleanly; rely on model default
    if conn.dialect.name != "sqlite":
        existing_indexes = [row[1] for row in conn.execute(sa.text("PRAGMA index_list(user_progress)")).fetchall()]
        if "uq_user_progress_user_lesson" not in existing_indexes:
            op.create_unique_constraint("uq_user_progress_user_lesson", "user_progress", ["user_id", "lesson_id"])


def downgrade():
    op.drop_constraint("uq_user_progress_user_lesson", "user_progress", type_="unique")
    op.drop_column("user_progress", "completed_at")
    op.drop_column("user_progress", "time_spent")
