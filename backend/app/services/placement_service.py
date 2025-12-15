from datetime import datetime
from math import ceil
from random import shuffle
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..db import models

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


def compute_level(score: int, total_questions: int = 20) -> str:
    normalized = score
    if total_questions and total_questions != 20:
        normalized = ceil(score * 20 / total_questions)
    if normalized >= 18:
        return "B2"
    if normalized >= 14:
        return "B1"
    if normalized >= 10:
        return "A2"
    if normalized >= 6:
        return "A1"
    return "A0"


def get_sections_for_age(age: int | None):
    is_kid = age is not None and age <= 15
    return [s for s in PLACEMENT_SECTIONS if not (s.get("age_group") == "adult" and is_kid)]


def build_questions(age: int | None) -> list[dict]:
    sections = get_sections_for_age(age)
    questions: list[dict] = []
    for section in sections:
        for q in section["questions"]:
            questions.append(
                {
                    "id": q["id"],
                    "prompt": q["question"],
                    "question": q["question"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "section": section["title"],
                }
            )
    return questions


def serialize_question(question: dict) -> dict:
    return {
        "id": question["id"],
        "prompt": question.get("prompt") or question.get("question"),
        "options": question.get("options") or [],
        "correct_option": question.get("correct"),
        "section": question.get("section"),
    }


def select_questions(age: int | None, limit: int = 20) -> list[dict]:
    questions = build_questions(age)
    shuffle(questions)
    selected = questions[: limit or len(questions)]
    return [serialize_question(q) for q in selected]


def start_run(session: dict, age: Optional[int]) -> dict:
    questions = build_questions(age)
    session["placement_run"] = {"idx": 0, "answers": []}
    return {
        "question": questions[0] if questions else None,
        "index": 1 if questions else 0,
        "total": len(questions),
    }


def next_question(session: dict, age: Optional[int]) -> dict:
    run = session.get("placement_run") or {}
    idx = int(run.get("idx") or 0)
    questions = build_questions(age)
    if idx >= len(questions):
        return {"done": True}
    question = questions[idx]
    question["prompt"] = question.get("prompt") or question.get("question")
    return {"question": question, "index": idx + 1, "total": len(questions)}


def answer_question(payload: Dict[str, Any], session: dict, user: Optional[models.User], db: Session, age: Optional[int]) -> dict:
    run = session.get("placement_run") or {}
    questions = build_questions(age)
    idx = int(run.get("idx") or 0)
    answers = run.get("answers") or []
    selected = payload.get("answer")

    if selected is None or idx >= len(questions):
        return {"error": "invalid_answer"}

    try:
        selected_idx = int(selected)
    except (TypeError, ValueError):
        selected_idx = None

    q = questions[idx]
    is_correct = selected_idx == q["correct"]
    answers.append({"id": q["id"], "selected": selected_idx, "correct": q["correct"], "is_correct": is_correct})
    idx += 1

    if idx >= len(questions):
        score = sum(1 for a in answers if a["is_correct"])
        total_questions = len(questions)
        normalized_score = ceil(score * 20 / total_questions) if total_questions else 0
        level = compute_level(score, total_questions)
        result_payload = {
            "score": normalized_score,
            "total": total_questions,
            "raw_score": score,
            "level": level,
        }
        session["placement_result"] = result_payload
        session.pop("placement_run", None)
        if user:
            record = models.PlacementTestResult(
                user_id=user.id,
                level=level,
                score=normalized_score,
                answers={"questions": answers, "total": total_questions, "raw_score": score},
                created_at=datetime.utcnow(),
            )
            db.add(record)
            user.level = level
            db.add(user)
            db.commit()
        return {"done": True, "result": result_payload}

    run = {"idx": idx, "answers": answers}
    session["placement_run"] = run
    next_q = questions[idx]
    next_q["prompt"] = next_q.get("prompt") or next_q.get("question")
    return {"question": next_q, "index": idx + 1, "total": len(questions)}


def score_answers(
    answers: list[dict],
    age: Optional[int],
    session_question_ids: list[str] | None = None,
) -> dict:
    question_map = {q["id"]: q for q in build_questions(age)}
    question_ids = session_question_ids or [a.get("question_id") for a in answers]

    scored: list[dict] = []
    for entry in answers:
        qid = entry.get("question_id")
        selected = entry.get("selected_option")
        question = question_map.get(qid)
        if not question:
            continue
        is_correct = selected is not None and int(selected) == int(question.get("correct"))
        scored.append(
            {
                "id": qid,
                "selected": selected,
                "correct": question.get("correct"),
                "is_correct": is_correct,
            }
        )

    raw_score = sum(1 for a in scored if a["is_correct"])
    total_questions = len(question_ids) if question_ids else len(scored)
    normalized_score = ceil(raw_score * 20 / total_questions) if total_questions else 0
    level = compute_level(raw_score, total_questions)

    return {
        "score": normalized_score,
        "total": total_questions,
        "raw_score": raw_score,
        "level": level,
        "answers": scored,
    }
