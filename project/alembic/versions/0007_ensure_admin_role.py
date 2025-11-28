"""ensure admin@example.com is admin"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_ensure_admin_role"
down_revision = "0006_update_user_progress"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET role = 'admin' WHERE email = :email"),
        {"email": "admin@example.com"},
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET role = 'user' WHERE email = :email AND role = 'admin'"),
        {"email": "admin@example.com"},
    )
