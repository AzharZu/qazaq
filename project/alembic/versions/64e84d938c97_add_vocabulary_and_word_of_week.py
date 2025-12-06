"""add_vocabulary_and_word_of_week

Revision ID: 64e84d938c97
Revises: 0008_add_user_dictionary
Create Date: 2025-12-02 08:43:57.759813

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64e84d938c97'
down_revision = '0008_add_user_dictionary'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vocabulary_words",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("translation", sa.String(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("example_sentence", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("learned", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("repeat_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mc_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("write_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vocabulary_words_user_id"), "vocabulary_words", ["user_id"], unique=False)
    op.create_index(op.f("ix_vocabulary_words_course_id"), "vocabulary_words", ["course_id"], unique=False)

    op.create_table(
        "word_of_the_week",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("stats_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stats_correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["word_id"], ["vocabulary_words.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # migrate legacy user_dictionary data if it exists
    conn = op.get_bind()
    try:
        conn.execute(
            sa.text(
                """
                INSERT INTO vocabulary_words (user_id, course_id, word, translation, definition, example_sentence, created_at)
                SELECT user_id, course_id, word, translation, translation, example, CURRENT_TIMESTAMP
                FROM user_dictionary
                """
            )
        )
    except Exception:
        # best-effort only
        pass


def downgrade():
    op.drop_table("word_of_the_week")
    op.drop_index(op.f("ix_vocabulary_words_course_id"), table_name="vocabulary_words")
    op.drop_index(op.f("ix_vocabulary_words_user_id"), table_name="vocabulary_words")
    op.drop_table("vocabulary_words")
