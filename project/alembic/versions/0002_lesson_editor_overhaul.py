"""Lesson editor overhaul: enforce ownership, ordering, and metadata for blocks and lessons."""

from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision = "0002_lesson_editor_overhaul"
down_revision = "64e84d938c97"
branch_labels = None
depends_on = None

ALLOWED_BLOCK_TYPES = (
    "theory",
    "example",
    "pronunciation",
    "flashcards",
    "quiz",
    "image",
    "audio",
    "assignment",
    "mascot_tip",
)


def _ensure_unassigned_lesson(connection) -> int:
    course_id = connection.execute(
        text("SELECT id FROM courses WHERE slug = :slug"),
        {"slug": "system-unassigned"},
    ).scalar()
    if not course_id:
        connection.execute(
            text(
                """
                INSERT INTO courses (slug, name, description, audience)
                VALUES (:slug, :name, :description, :audience)
                """
            ),
            {
                "slug": "system-unassigned",
                "name": "System Unassigned",
                "description": "Container course for orphaned blocks",
                "audience": "adult",
            },
        )
        course_id = connection.execute(
            text("SELECT id FROM courses WHERE slug = :slug"),
            {"slug": "system-unassigned"},
        ).scalar()

    module_id = connection.execute(
        text("SELECT id FROM modules WHERE course_id = :course_id AND name = :name"),
        {"course_id": course_id, "name": "Unassigned"},
    ).scalar()
    if not module_id:
        connection.execute(
            text(
                """
                INSERT INTO modules (course_id, name, "order", description)
                VALUES (:course_id, :name, :order, :description)
                """
            ),
            {
                "course_id": course_id,
                "name": "Unassigned",
                "order": 9999,
                "description": "Auto-generated module for orphaned blocks",
            },
        )
        module_id = connection.execute(
            text("SELECT id FROM modules WHERE course_id = :course_id AND name = :name"),
            {"course_id": course_id, "name": "Unassigned"},
        ).scalar()

    lesson_id = connection.execute(
        text("SELECT id FROM lessons WHERE module_id = :module_id AND title = :title"),
        {"module_id": module_id, "title": "Unassigned Blocks"},
    ).scalar()
    if not lesson_id:
        now = datetime.utcnow()
        connection.execute(
            text(
                """
                INSERT INTO lessons (
                    module_id, title, description, lesson_type, estimated_time, difficulty,
                    age_group, "order", status, language, version, created_at, updated_at
                )
                VALUES (
                    :module_id, :title, :description, :lesson_type, :estimated_time, :difficulty,
                    :age_group, :order, :status, :language, :version, :created_at, :updated_at
                )
                """
            ),
            {
                "module_id": module_id,
                "title": "Unassigned Blocks",
                "description": "Auto-created lesson for orphan blocks",
                "lesson_type": "maintenance",
                "estimated_time": None,
                "difficulty": None,
                "age_group": None,
                "order": 9999,
                "status": "draft",
                "language": "kk",
                "version": 1,
                "created_at": now,
                "updated_at": now,
            },
        )
        lesson_id = connection.execute(
            text("SELECT id FROM lessons WHERE module_id = :module_id AND title = :title"),
            {"module_id": module_id, "title": "Unassigned Blocks"},
        ).scalar()
    return lesson_id


def _resequence_block_orders(connection):
    connection.execute(
        text(
            """
            WITH ordered AS (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY lesson_id ORDER BY "order", id) AS rn
                FROM lesson_blocks
            )
            UPDATE lesson_blocks
            SET "order" = (SELECT rn FROM ordered WHERE ordered.id = lesson_blocks.id)
            """
        )
    )


def _coerce_invalid_block_types(connection):
    allowed_csv = ",".join(f"'{t}'" for t in ALLOWED_BLOCK_TYPES)
    connection.execute(
        text(
            f"UPDATE lesson_blocks SET block_type = 'theory' WHERE block_type NOT IN ({allowed_csv}) OR block_type IS NULL"
        )
    )


def _create_block_type_constraints(connection):
    dialect = connection.dialect.name
    allowed_csv = ",".join(f"'{t}'" for t in ALLOWED_BLOCK_TYPES)
    if dialect == "sqlite":
        connection.execute(
            text(
                f"""
                CREATE TRIGGER IF NOT EXISTS trg_lesson_blocks_type_insert
                BEFORE INSERT ON lesson_blocks
                WHEN NEW.block_type NOT IN ({allowed_csv}) OR NEW.block_type IS NULL
                BEGIN
                    SELECT RAISE(ABORT, 'invalid block_type');
                END;
                """
            )
        )
        connection.execute(
            text(
                f"""
                CREATE TRIGGER IF NOT EXISTS trg_lesson_blocks_type_update
                BEFORE UPDATE ON lesson_blocks
                WHEN NEW.block_type NOT IN ({allowed_csv}) OR NEW.block_type IS NULL
                BEGIN
                    SELECT RAISE(ABORT, 'invalid block_type');
                END;
                """
            )
        )
    else:
        enum_type = sa.Enum(*ALLOWED_BLOCK_TYPES, name="block_type_enum")
        enum_type.create(op.get_bind(), checkfirst=True)
        op.alter_column(
            "lesson_blocks",
            "block_type",
            existing_type=sa.String(),
            type_=enum_type,
            nullable=False,
            existing_nullable=False,
        )


def _drop_block_type_constraints(connection):
    dialect = connection.dialect.name
    if dialect == "sqlite":
        connection.execute(text("DROP TRIGGER IF EXISTS trg_lesson_blocks_type_insert"))
        connection.execute(text("DROP TRIGGER IF EXISTS trg_lesson_blocks_type_update"))
    else:
        enum_type = sa.Enum(*ALLOWED_BLOCK_TYPES, name="block_type_enum")
        op.alter_column(
            "lesson_blocks",
            "block_type",
            existing_type=enum_type,
            type_=sa.String(),
            nullable=False,
            existing_nullable=False,
        )
        enum_type.drop(op.get_bind(), checkfirst=True)


def upgrade():
    connection = op.get_bind()
    inspector = inspect(connection)
    lesson_cols = {col["name"] for col in inspector.get_columns("lessons")}

    if "status" not in lesson_cols:
        op.add_column("lessons", sa.Column("status", sa.String(), nullable=False, server_default="draft"))
    if "language" not in lesson_cols:
        op.add_column("lessons", sa.Column("language", sa.String(), nullable=False, server_default="kk"))
    if "version" not in lesson_cols:
        op.add_column("lessons", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    if "created_at" not in lesson_cols:
        op.add_column("lessons", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    if "updated_at" not in lesson_cols:
        op.add_column("lessons", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))

    target_lesson = _ensure_unassigned_lesson(connection)

    connection.execute(
        text("UPDATE lesson_blocks SET lesson_id = :lesson_id WHERE lesson_id IS NULL"),
        {"lesson_id": target_lesson},
    )

    dialect = connection.dialect.name
    if dialect != "sqlite":
        op.alter_column("lesson_blocks", "lesson_id", existing_type=sa.Integer(), nullable=False)

    _coerce_invalid_block_types(connection)
    _create_block_type_constraints(connection)
    _resequence_block_orders(connection)

    if dialect == "sqlite":
        op.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_lesson_blocks_lesson_order ON lesson_blocks(lesson_id, "order")')
    else:
        op.create_unique_constraint("uq_lesson_blocks_lesson_order", "lesson_blocks", ["lesson_id", "order"])


def downgrade():
    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "sqlite":
        op.execute('DROP INDEX IF EXISTS uq_lesson_blocks_lesson_order')
    else:
        op.drop_constraint("uq_lesson_blocks_lesson_order", "lesson_blocks", type_="unique")

    _drop_block_type_constraints(connection)
    if dialect != "sqlite":
        op.alter_column("lesson_blocks", "lesson_id", existing_type=sa.Integer(), nullable=True)

    op.drop_column("lessons", "updated_at")
    op.drop_column("lessons", "created_at")
    op.drop_column("lessons", "version")
    op.drop_column("lessons", "language")
    op.drop_column("lessons", "status")
