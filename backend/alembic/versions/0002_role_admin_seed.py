from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '0002_role_admin_seed'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def _ensure_unassigned_lesson(connection) -> int:
    return None


def upgrade():
    connection = op.get_bind()

    connection.execute(
        text("""
            INSERT INTO roles (name, description)
            VALUES ('admin', 'Administrator role with full permissions')
            ON CONFLICT (name) DO NOTHING;
        """)
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(text("DELETE FROM roles WHERE name = 'admin'"))