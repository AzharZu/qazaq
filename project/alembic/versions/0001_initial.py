"""create core tables and seed data"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Text, JSON, DateTime

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("age", sa.Integer, nullable=False),
        sa.Column("target", sa.String, nullable=False),
        sa.Column("daily_minutes", sa.Integer, nullable=False, server_default="10"),
        sa.Column("level", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "placement_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("level", sa.String, nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("audience", sa.String, nullable=False),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("course_id", sa.Integer, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="1"),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("module_id", sa.Integer, sa.ForeignKey("modules.id"), nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("lesson_type", sa.String, nullable=True),
        sa.Column("estimated_time", sa.Integer, nullable=True),
        sa.Column("difficulty", sa.String, nullable=True),
        sa.Column("age_group", sa.String, nullable=True),
        sa.Column("order", sa.Integer, nullable=False, server_default="1"),
    )

    op.create_table(
        "lesson_blocks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("block_type", sa.String, nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="1"),
    )

    op.create_table(
        "flashcards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("front", sa.String, nullable=False),
        sa.Column("back", sa.String, nullable=False),
        sa.Column("image_url", sa.String, nullable=True),
        sa.Column("audio_url", sa.String, nullable=True),
        sa.Column("age_group", sa.String, nullable=True),
    )

    op.create_table(
        "quizzes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("options", sa.JSON, nullable=False),
        sa.Column("correct_option", sa.Integer, nullable=False),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("age_group", sa.String, nullable=True),
    )

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="not_started"),
        sa.Column("last_opened_at", sa.DateTime, nullable=True, server_default=sa.func.now()),
    )

    courses_table = table(
        "courses",
        column("id", Integer),
        column("slug", String),
        column("name", String),
        column("description", Text),
        column("audience", String),
    )

    op.bulk_insert(
        courses_table,
        [
            {
                "id": 1,
                "slug": "kazkids",
                "name": "KazKids",
                "description": "Игровое изучение казахского языка для детей и школьников.",
                "audience": "kids",
            },
            {
                "id": 2,
                "slug": "kazpro",
                "name": "KazPro",
                "description": "Практический курс для взрослых: диалоги, грамматика и культура.",
                "audience": "adult",
            },
            {
                "id": 3,
                "slug": "qyzmet-qazaq",
                "name": "Qyzmet Qazaq",
                "description": "Официальный стиль для госслужащих: письма, телефонный этикет, протокол.",
                "audience": "gov",
            },
        ],
    )

    modules_table = table(
        "modules",
        column("id", Integer),
        column("course_id", Integer),
        column("name", String),
        column("order", Integer),
        column("description", Text),
    )

    op.bulk_insert(
        modules_table,
        [
            {"id": 1, "course_id": 1, "name": "Әліппе", "order": 1, "description": "Знакомство с буквами и звуками"},
            {"id": 2, "course_id": 1, "name": "Түстер мен жануарлар", "order": 2, "description": "Слова через игры"},
            {"id": 3, "course_id": 2, "name": "Повседневные диалоги", "order": 1, "description": "Приветствия, знакомства"},
            {"id": 4, "course_id": 2, "name": "Грамматика для жизни", "order": 2, "description": "Время, движение, планы"},
            {"id": 5, "course_id": 3, "name": "Ресми хаттар", "order": 1, "description": "Письма и служебные записки"},
            {"id": 6, "course_id": 3, "name": "Этикет", "order": 2, "description": "Телефон, встречи, приветствие"},
        ],
    )

    lessons_table = table(
        "lessons",
        column("id", Integer),
        column("module_id", Integer),
        column("title", String),
        column("description", Text),
        column("lesson_type", String),
        column("estimated_time", Integer),
        column("difficulty", String),
        column("age_group", String),
        column("order", Integer),
    )

    op.bulk_insert(
        lessons_table,
        [
            {
                "id": 1,
                "module_id": 1,
                "title": "Казахский алфавит",
                "description": "Знакомство с дыбыстар мен әріптер",
                "lesson_type": "theory",
                "estimated_time": 10,
                "difficulty": "easy",
                "age_group": "kids",
                "order": 1,
            },
            {
                "id": 2,
                "module_id": 2,
                "title": "Түстер және жануарлар",
                "description": "Учимся описывать картинки",
                "lesson_type": "practice",
                "estimated_time": 12,
                "difficulty": "easy",
                "age_group": "kids",
                "order": 1,
            },
            {
                "id": 3,
                "module_id": 3,
                "title": "Приветствия и знакомства",
                "description": "Этикет и сценарии знакомства",
                "lesson_type": "dialogue",
                "estimated_time": 15,
                "difficulty": "medium",
                "age_group": "adult",
                "order": 1,
            },
            {
                "id": 4,
                "module_id": 4,
                "title": "Планы и время",
                "description": "Рассказываем о планах и предпочитаемом времени",
                "lesson_type": "grammar",
                "estimated_time": 15,
                "difficulty": "medium",
                "age_group": "adult",
                "order": 1,
            },
            {
                "id": 5,
                "module_id": 5,
                "title": "Служебное письмо",
                "description": "Официальный стиль: шаблоны писем",
                "lesson_type": "official",
                "estimated_time": 18,
                "difficulty": "medium",
                "age_group": "gov",
                "order": 1,
            },
            {
                "id": 6,
                "module_id": 6,
                "title": "Телефонный звонок",
                "description": "Диалог по телефону в официальном стиле",
                "lesson_type": "official",
                "estimated_time": 12,
                "difficulty": "medium",
                "age_group": "gov",
                "order": 1,
            },
        ],
    )

    lesson_blocks_table = table(
        "lesson_blocks",
        column("id", Integer),
        column("lesson_id", Integer),
        column("block_type", String),
        column("content", JSON),
        column("order", Integer),
    )

    op.bulk_insert(
        lesson_blocks_table,
        [
            {
                "id": 1,
                "lesson_id": 1,
                "block_type": "theory",
                "content": {"title": "Әліппе", "text": "Әліпби 42 әріптен тұрады. Дауысты мен дауыссыз дыбыстар."},
                "order": 1,
            },
            {
                "id": 2,
                "lesson_id": 1,
                "block_type": "example",
                "content": {"rows": [{"kz": "Аа - алма", "ru": "яблоко"}, {"kz": "Бб - бала", "ru": "ребенок"}]},
                "order": 2,
            },
            {
                "id": 3,
                "lesson_id": 1,
                "block_type": "mascot_tip",
                "content": {"text": "Айтылымды дауыстап үнемі қайталаңыз!", "icon": "🦊"},
                "order": 3,
            },
            {
                "id": 4,
                "lesson_id": 2,
                "block_type": "flashcards",
                "content": {"title": "Түстерді жаттаймыз"},
                "order": 1,
            },
            {
                "id": 5,
                "lesson_id": 2,
                "block_type": "quiz",
                "content": {"title": "Жануарларды тап"},
                "order": 2,
            },
            {
                "id": 6,
                "lesson_id": 3,
                "block_type": "story",
                "content": {
                    "dialogue": [
                        {"speaker": "Айгерім", "line": "Сәлеметсіз бе! Мен Айгерім."},
                        {"speaker": "Тимур", "line": "Қуаныштымын, Тимурмын."},
                        {"speaker": "Айгерім", "line": "Қайда жұмыс істейсіз?"},
                        {"speaker": "Тимур", "line": "Мен айти саласында."},
                    ]
                },
                "order": 1,
            },
            {
                "id": 7,
                "lesson_id": 3,
                "block_type": "theory",
                "content": {"title": "Құрметті / Сәлеметсіз бе", "text": "Регистр обращения вежливый и дружеский."},
                "order": 2,
            },
            {
                "id": 8,
                "lesson_id": 4,
                "block_type": "theory",
                "content": {"title": "Келер шақ", "text": "Ертең, келесі апта сияқты маркерлер жоспарда."},
                "order": 1,
            },
            {
                "id": 9,
                "lesson_id": 4,
                "block_type": "example",
                "content": {
                    "rows": [
                        {"kz": "Мен ертең жиналысқа барамын", "ru": "Я завтра пойду на встречу"},
                        {"kz": "Біз кешке қоңырау шаламыз", "ru": "Мы позвоним вечером"},
                    ]
                },
                "order": 2,
            },
            {
                "id": 10,
                "lesson_id": 5,
                "block_type": "theory",
                "content": {
                    "title": "Ресми тіркестер",
                    "text": "«Құрметті», «қоса беріліп отыр», «құрметпен» – базовые клише.",
                },
                "order": 1,
            },
            {
                "id": 11,
                "lesson_id": 5,
                "block_type": "quiz",
                "content": {"title": "Письмо: что подходит?"},
                "order": 2,
            },
            {
                "id": 12,
                "lesson_id": 6,
                "block_type": "theory",
                "content": {"title": "Телефон этикеті", "text": "Сәлемдесу, таныстыру, мақсатты қысқа айту."},
                "order": 1,
            },
            {
                "id": 13,
                "lesson_id": 6,
                "block_type": "story",
                "content": {
                    "dialogue": [
                        {"speaker": "Канат", "line": "Қайырлы күн, Қаржы министрлігінен қоңырау шалып тұрмын."},
                        {"speaker": "Әлия", "line": "Қайырлы күн, тыңдап тұрмын."},
                        {"speaker": "Канат", "line": "Кездесуді бейсенбіге ауыстырсақ."},
                    ]
                },
                "order": 2,
            },
        ],
    )

    flashcards_table = table(
        "flashcards",
        column("id", Integer),
        column("lesson_id", Integer),
        column("front", String),
        column("back", String),
        column("image_url", String),
        column("audio_url", String),
        column("age_group", String),
    )

    op.bulk_insert(
        flashcards_table,
        [
            {"id": 1, "lesson_id": 2, "front": "көк", "back": "синий", "image_url": None, "audio_url": None, "age_group": "kids"},
            {"id": 2, "lesson_id": 2, "front": "қызыл", "back": "красный", "image_url": None, "audio_url": None, "age_group": "kids"},
            {"id": 3, "lesson_id": 2, "front": "ақ", "back": "белый", "image_url": None, "audio_url": None, "age_group": "kids"},
            {"id": 4, "lesson_id": 3, "front": "Сәлеметсіз бе?", "back": "Здравствуйте", "image_url": None, "audio_url": None, "age_group": "adult"},
            {"id": 5, "lesson_id": 3, "front": "Қалайсыңыз?", "back": "Как вы?", "image_url": None, "audio_url": None, "age_group": "adult"},
        ],
    )

    quizzes_table = table(
        "quizzes",
        column("id", Integer),
        column("lesson_id", Integer),
        column("question", Text),
        column("options", JSON),
        column("correct_option", Integer),
        column("explanation", Text),
        column("age_group", String),
    )

    op.bulk_insert(
        quizzes_table,
        [
            {
                "id": 1,
                "lesson_id": 2,
                "question": "Қай суретте «қасқыр»?",
                "options": ["wolf.png", "cat.png", "dog.png"],
                "correct_option": 0,
                "explanation": "Қасқыр — дала қасқыры, алғашқы сурет.",
                "age_group": "kids",
            },
            {
                "id": 2,
                "lesson_id": 3,
                "question": "Как спросить имя вежливо?",
                "options": ["Сен кімсің?", "Атыңыз кім?", "Кім боласыз?"],
                "correct_option": 1,
                "explanation": "Вежливое обращение требует формы -ңыз/-ңіз.",
                "age_group": "adult",
            },
            {
                "id": 3,
                "lesson_id": 4,
                "question": "Продолжите: Мен _____ жиналысқа барамын",
                "options": ["ертең", "кеше", "бүгін"],
                "correct_option": 0,
                "explanation": "Ертең — будущие планы.",
                "age_group": "adult",
            },
            {
                "id": 4,
                "lesson_id": 5,
                "question": "Как завершить письмо?",
                "options": ["Көріскенше!", "Құрметпен", "Пока"],
                "correct_option": 1,
                "explanation": "Официальный конец — «Құрметпен».",
                "age_group": "gov",
            },
            {
                "id": 5,
                "lesson_id": 6,
                "question": "Первое действие при звонке?",
                "options": ["Сразу задаем вопрос", "Приветствуем и представляемся", "Просим перезвонить"],
                "correct_option": 1,
                "explanation": "Этикет требует приветствия и представления.",
                "age_group": "gov",
            },
        ],
    )


def downgrade():
    op.drop_table("user_progress")
    op.drop_table("quizzes")
    op.drop_table("flashcards")
    op.drop_table("lesson_blocks")
    op.drop_table("lessons")
    op.drop_table("modules")
    op.drop_table("courses")
    op.drop_table("placement_results")
    op.drop_table("users")
