"""add user dictionary"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_add_user_dictionary"
down_revision = "0007_ensure_admin_role"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_dictionary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("translation", sa.String(), nullable=False),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_dictionary_user", "user_dictionary", ["user_id"])


def downgrade():
    op.drop_index("ix_user_dictionary_user", table_name="user_dictionary")
    op.drop_table("user_dictionary")
