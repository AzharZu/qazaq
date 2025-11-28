PLACEMENT_SECTIONS = [
    {
        "key": "lexis",
        "title": "Лексика",
        "questions": [
            {"id": "lex_1", "question": "Қалайсың? (ответ: Как дела?)", "options": ["Спасибо", "Хорошо", "Плохо"], "correct": 1},
            {"id": "lex_2", "question": "Сөз «мектеп» означает...", "options": ["школа", "книга", "дом"], "correct": 0},
            {"id": "lex_3", "question": "Қайсысы түстер?", "options": ["көк, қызыл", "ыстық, суық", "жақсы, жаман"], "correct": 0},
            {"id": "lex_4", "question": "Сан «жеті» это...", "options": ["6", "7", "8"], "correct": 1},
            {"id": "lex_5", "question": "«Дос» переводится как", "options": ["друг", "дело", "урок"], "correct": 0},
        ],
    },
    {
        "key": "grammar",
        "title": "Грамматика",
        "questions": [
            {"id": "gr_1", "question": "Правильная форма мн. числа: кітап — ...", "options": ["кітаптар", "кітаплар", "кітапдер"], "correct": 0},
            {"id": "gr_2", "question": "«Мен бардым» означает", "options": ["Я иду", "Я ходил", "Я пойду"], "correct": 1},
            {"id": "gr_3", "question": "Будущее время: біз ... оқимыз", "options": ["кеше", "бүгін", "ертең"], "correct": 2},
            {"id": "gr_4", "question": "Выберите послелог направления", "options": ["үшін", "қарай", "сияқты"], "correct": 1},
            {"id": "gr_5", "question": "Правильное окончание род. падежа: қала...", "options": ["ның", "ға", "мен"], "correct": 0},
        ],
    },
    {
        "key": "reading",
        "title": "Чтение",
        "questions": [
            {"id": "rd_1", "question": "«Мен қазақ тілін үйренемін»", "options": ["Я учу казахский язык", "Я говорю по-казахски", "Я поеду в Казахстан"], "correct": 0},
            {"id": "rd_2", "question": "«Студент кітап оқып отыр»", "options": ["Студент читает", "Студент пишет", "Студент спит"], "correct": 0},
            {"id": "rd_3", "question": "«Бұл - менің отбасым»", "options": ["Это моя семья", "Это моя книга", "Это мой город"], "correct": 0},
            {"id": "rd_4", "question": "«Жұмыс уақыты 9-дан 6-ға дейін»", "options": ["С 9 до 6", "С 6 до 9", "Круглосуточно"], "correct": 0},
            {"id": "rd_5", "question": "«Сабақ онлайн өтеді»", "options": ["Урок проходит онлайн", "Урок отменён", "Урок в классе"], "correct": 0},
        ],
    },
    {
        "key": "formal",
        "title": "Формально-деловой стиль",
        "age_group": "adult",
        "questions": [
            {"id": "fm_1", "question": "Правильное обращение в письме госоргану", "options": ["Сәлем!", "Құрметті әріптестер!", "Салем дос!"], "correct": 1},
            {"id": "fm_2", "question": "«Арыз» — это", "options": ["жалоба/заявление", "приглашение", "отчёт"], "correct": 0},
            {"id": "fm_3", "question": "Официальное «please find attached»", "options": ["қоса беріліп отыр", "алдым", "оқыдым"], "correct": 0},
            {"id": "fm_4", "question": "«Ұсыныс хат» означает", "options": ["рекомендация", "согласование", "причина"], "correct": 0},
            {"id": "fm_5", "question": "Стандартное завершение письма", "options": ["Көріскенше!", "Құрметпен", "Пока"], "correct": 1},
        ],
    },
]


def get_sections_for_age(age: int | None):
    is_kid = age is not None and age <= 15
    return [s for s in PLACEMENT_SECTIONS if not (s.get("age_group") == "adult" and is_kid)]
