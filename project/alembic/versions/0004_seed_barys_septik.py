"""seed kazkids barys septik lesson with blocks, flashcards, quizzes"""

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "0004_seed_barys_septik"
down_revision = "0003_rehash_admin_pbkdf2"
branch_labels = None
depends_on = None


def _get_scalar(conn, query, params):
    result = conn.execute(text(query), params).scalar()
    return result


def upgrade():
    conn = op.get_bind()

    course_id = _get_scalar(conn, "SELECT id FROM courses WHERE slug = :slug", {"slug": "kazkids"})
    if not course_id:
        return

    module_id = _get_scalar(
        conn,
        "SELECT id FROM modules WHERE course_id = :cid AND name = :name",
        {"cid": course_id, "name": "Септіктер"},
    )
    if not module_id:
        conn.execute(
            text(
                "INSERT INTO modules (course_id, name, `order`, description) VALUES (:cid, :name, :order, :desc)"
            ),
            {"cid": course_id, "name": "Септіктер", "order": 3, "desc": "Қазақ тіліндегі септіктер"},
        )
        module_id = _get_scalar(conn, "SELECT id FROM modules WHERE course_id=:cid AND name=:name", {"cid": course_id, "name": "Септіктер"})

    lesson_id = _get_scalar(
        conn,
        "SELECT id FROM lessons WHERE module_id=:mid AND title=:title",
        {"mid": module_id, "title": "Барыс септік"},
    )
    if not lesson_id:
        conn.execute(
            text(
                """
                INSERT INTO lessons (module_id, title, description, lesson_type, estimated_time, difficulty, age_group, `order`)
                VALUES (:mid, :title, :desc, :lt, :time, :diff, :age, :ord)
                """
            ),
            {
                "mid": module_id,
                "title": "Барыс септік",
                "desc": "Бағытты білдіретін септік: сұрақтары — қайда? кімге? неге?",
                "lt": "mixed",
                "time": 5,
                "diff": "easy",
                "age": "kids",
                "ord": 1,
            },
        )
        lesson_id = _get_scalar(conn, "SELECT id FROM lessons WHERE module_id=:mid AND title=:title", {"mid": module_id, "title": "Барыс септік"})

    # Flashcards
    flashcards_exist = _get_scalar(conn, "SELECT COUNT(1) FROM flashcards WHERE lesson_id=:lid", {"lid": lesson_id})
    if not flashcards_exist:
        flashcards_data = [
            ("мектеп", "школа → мектепке"),
            ("әже", "бабушка → әжеге"),
            ("үй", "дом → үйге"),
            ("дәрігер", "врач → дәрігерге"),
            ("дүкен", "магазин → дүкенге"),
        ]
        for idx, (front, back) in enumerate(flashcards_data, start=1):
            conn.execute(
                text(
                    """
                    INSERT INTO flashcards (lesson_id, front, back, image_url, audio_url, age_group, `order`)
                    VALUES (:lid, :front, :back, NULL, NULL, :age, :ord)
                    """
                ),
                {"lid": lesson_id, "front": front, "back": back, "age": "kids", "ord": idx},
            )
    flashcard_ids = [
        row[0]
        for row in conn.execute(
            text("SELECT id FROM flashcards WHERE lesson_id=:lid ORDER BY `order`"), {"lid": lesson_id}
        ).fetchall()
    ]

    # Quizzes
    quizzes_exist = _get_scalar(conn, "SELECT COUNT(1) FROM quizzes WHERE lesson_id=:lid", {"lid": lesson_id})
    if not quizzes_exist:
        quizzes = [
            (
                "Дұрыс нұсқаны таңда: Мен ... барамын.",
                ["мектепте", "мектепке", "мектептен"],
                1,
                "Бағыт → мектепке",
            ),
            (
                "Қайсысы дұрыс?",
                ["Әжеме хат жаздым.", "Әже хат жаздым.", "Әжеге хат жаздымм."],
                0,
                "«Әжеме хат жаздым» — дұрыс барыс септік.",
            ),
            (
                "Сөйлемді толтыр: Мен саба__ кешігіп келдім.",
                ["қе", "ға", "ге"],
                2,
                "Сабақ → сабаққа. Дұрыс жалғау — -қа, бірақ жазылуы 'сабаққа'.",
            ),
        ]
        for idx, (question, options, correct, expl) in enumerate(quizzes, start=1):
            conn.execute(
                text(
                    """
                    INSERT INTO quizzes (lesson_id, question, options, correct_option, explanation, age_group, `order`)
                    VALUES (:lid, :q, :opts, :correct, :expl, :age, :ord)
                    """
                ),
                {
                    "lid": lesson_id,
                    "q": question,
                    "opts": json.dumps(options),
                    "correct": correct,
                    "expl": expl,
                    "age": "kids",
                    "ord": idx,
                },
            )

    quiz_ids = [
        row[0]
        for row in conn.execute(
            text("SELECT id FROM quizzes WHERE lesson_id=:lid ORDER BY `order`"), {"lid": lesson_id}
        ).fetchall()
    ]

    blocks_exist = _get_scalar(conn, "SELECT COUNT(1) FROM lesson_blocks WHERE lesson_id=:lid", {"lid": lesson_id})
    if blocks_exist:
        return

    blocks = [
        (
            "theory",
            1,
            {
                "title": "Барыс септік деген не?",
                "text": "Барыс септік бағытты білдіреді. Сұрақтары: қайда? кімге? неге? Сөз соңына -ға/-ге, -қа/-ке жалғаулары жалғанады.",
            },
        ),
        (
            "example",
            2,
            {
                "examples": [
                    {"kz": "Мен мектепке барамын.", "ru": "Я иду в школу."},
                    {"kz": "Әжеме хат жаздым.", "ru": "Я написал бабушке письмо."},
                    {"kz": "Мен сабаққа кешігіп келдім.", "ru": "Я опоздал на урок."},
                ]
            },
        ),
        ("mascot_tip", 3, {"text": "Ереже: Егер сөз жіңішке болса — -ге/-ке, ал жуан болса — -ға/-қа.", "icon": "🦊"}),
        ("flashcards", 4, {"flashcard_ids": flashcard_ids}),
        ("quiz", 5, {"quiz_ids": quiz_ids}),
        ("pronunciation", 6, {"title": "Қиын дыбыстарды айтайық", "words": ["әже", "өрік", "ұл", "қала", "жаңа", "оң"]}),
    ]

    for block_type, order, content in blocks:
        conn.execute(
            text(
                """
                INSERT INTO lesson_blocks (lesson_id, block_type, content, `order`)
                VALUES (:lid, :type, :content, :ord)
                """
            ),
            {"lid": lesson_id, "type": block_type, "content": json.dumps(content), "ord": order},
        )


def downgrade():
    conn = op.get_bind()
    lesson_id = _get_scalar(conn, "SELECT id FROM lessons WHERE title=:title", {"title": "Барыс септік"})
    if lesson_id:
        conn.execute(text("DELETE FROM lesson_blocks WHERE lesson_id=:lid"), {"lid": lesson_id})
        conn.execute(text("DELETE FROM flashcards WHERE lesson_id=:lid"), {"lid": lesson_id})
        conn.execute(text("DELETE FROM quizzes WHERE lesson_id=:lid"), {"lid": lesson_id})
        conn.execute(text("DELETE FROM lessons WHERE id=:lid"), {"lid": lesson_id})
