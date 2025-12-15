"""Add level test, progress tables, certificates, dictionary image"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251220_add_level_test_and_progress_tables"
down_revision = "20251216_add_user_progress_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "level_test_questions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("correct_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "level_test_options",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("level_test_questions.id"), nullable=False, index=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "user_lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id"), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="in_progress"),
        sa.Column("completed_blocks", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "user_course_progress",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False, index=True),
        sa.Column("percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False, index=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    # Extend dictionary with image_url
    with op.batch_alter_table("user_dictionary") as batch:
        batch.add_column(sa.Column("image_url", sa.String(), nullable=True))
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("full_name", sa.String(), nullable=True))
        batch.add_column(sa.Column("photo_url", sa.String(), nullable=True))
        batch.add_column(sa.Column("language", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("language")
        batch.drop_column("photo_url")
        batch.drop_column("full_name")
    with op.batch_alter_table("user_dictionary") as batch:
        batch.drop_column("image_url")
    op.drop_table("certificates")
    op.drop_table("user_course_progress")
    op.drop_table("user_lesson_progress")
    op.drop_table("level_test_options")
    op.drop_table("level_test_questions")
