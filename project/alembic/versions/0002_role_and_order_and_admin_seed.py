"""add role to users, order to flashcards/quizzes, seed admin"""

from alembic import op
import sqlalchemy as sa
from passlib.hash import pbkdf2_sha256

# revision identifiers, used by Alembic.
revision = "0002_role_and_order_and_admin_seed"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="user"))
    op.add_column("flashcards", sa.Column("order", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("quizzes", sa.Column("order", sa.Integer(), nullable=False, server_default="1"))

    conn = op.get_bind()
    hashed = pbkdf2_sha256.hash("admin123")
    conn.execute(
        sa.text(
            """
            INSERT INTO users (email, hashed_password, age, target, daily_minutes, level, role)
            VALUES (:email, :pwd, :age, :target, :minutes, :level, :role)
            """
        ),
        {
            "email": "admin@example.com",
            "pwd": hashed,
            "age": 30,
            "target": "business",
            "minutes": 30,
            "level": "B2",
            "role": "admin",
        },
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email = :email"), {"email": "admin@example.com"})
    op.drop_column("quizzes", "order")
    op.drop_column("flashcards", "order")
    op.drop_column("users", "role")
