"""rehash admin password to pbkdf2 to avoid bcrypt backend issues"""

from alembic import op
from passlib.hash import pbkdf2_sha256
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_rehash_admin_pbkdf2"
down_revision = "0002_role_admin_seed"
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
    # No downgrade because original bcrypt hash depended on environment backend
    pass
