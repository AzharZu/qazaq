"""Create daily_goals table"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260304_add_daily_goals_table"
down_revision = "20250213_add_audio_path_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_goals",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("goal_type", sa.String(), nullable=False, server_default="light"),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("completed_today", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            server_onupdate=sa.text("now()"),
        ),
    )
    op.create_index(op.f("ix_daily_goals_user_id"), "daily_goals", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_daily_goals_user_id"), table_name="daily_goals")
    op.drop_table("daily_goals")
