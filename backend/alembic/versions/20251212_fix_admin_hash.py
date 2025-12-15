"""Rehash admin password with valid scheme

Ensures admin@example.com has a valid passlib hash (pbkdf2_sha256).
"""

from alembic import op
from passlib.hash import pbkdf2_sha256
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251212_fix_admin_hash"
down_revision = "20251211_merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    new_hash = pbkdf2_sha256.hash("admin123")
    conn.execute(
        sa.text("UPDATE users SET hashed_password = :pwd WHERE email = :email"),
        {"pwd": new_hash, "email": "admin@example.com"},
    )


def downgrade():
    # No safe downgrade to previous hash (it was invalid/truncated), so leave as-is.
    pass
