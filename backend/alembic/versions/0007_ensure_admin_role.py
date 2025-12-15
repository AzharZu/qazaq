"""ensure admin@example.com is admin"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_ensure_admin_role"
down_revision = "0002_role_admin_seed"
branch_labels = None
depends_on = None


def upgrade():
    # Add role column if it doesn't exist yet (older initial schema lacked it)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "role" not in columns:
        op.add_column(
            "users",
            sa.Column("role", sa.String(), nullable=False, server_default="user"),
        )
    if conn.dialect.name != "sqlite":
        op.alter_column("users", "role", server_default=None)
    else:
        # SQLite lacks ALTER COLUMN DROP DEFAULT; defaults on new rows are fine.
        pass

    conn.execute(
        sa.text("UPDATE users SET role = 'admin' WHERE email = :email"),
        {"email": "admin@example.com"},
    )


def downgrade():
    # Revert role values and drop column for clean rollback
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET role = 'user' WHERE email = :email AND role = 'admin'"),
        {"email": "admin@example.com"},
    )
    op.drop_column("users", "role")
