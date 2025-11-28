from typing import List

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import compute_level, recommend_course_slug
from ..services.placement_questions import PLACEMENT_SECTIONS, get_sections_for_age
from ..templating import render_template

router = APIRouter(tags=["placement"])

LEVEL_DESCRIPTIONS = {
    "A0": "Стартовый уровень: знакомство с алфавитом и базовыми словами.",
    "A1": "Начинающий: понимаете простые фразы, умеете представиться.",
    "A2": "Элементарный: строите короткие фразы, спрашиваете дорогу, планируете день.",
    "B1": "Средний: поддерживаете беседу, понимаете тексты о работе/учёбе.",
    "B2": "Продвинутый: свободно читаете и общаетесь в большинстве ситуаций.",
}


def _load_user(request: Request, db: Session) -> models.User | None:
    user = getattr(request.state, "user", None)
    if user:
        return db.get(models.User, user.id)
    return None


def _build_questions(age: int | None) -> List[dict]:
    sections = get_sections_for_age(age)
    questions: List[dict] = []
    for section in sections:
        for q in section["questions"]:
            questions.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "section": section["title"],
                }
            )
    return questions


@router.get("/placement-test")
async def placement_get(request: Request, db: Session = Depends(get_db)):
    user = _load_user(request, db)
    age = user.age if user else None

    questions = _build_questions(age)
    run = request.session.get("placement_run") or {}
    idx = int(run.get("idx") or 0)
    answers = run.get("answers") or []
    if idx < 0:
        idx = 0
    if idx >= len(questions):
        idx = 0
        answers = []
    request.session["placement_run"] = {"idx": idx, "answers": answers}

    q = questions[idx] if idx < len(questions) else None
    if not q:
        return RedirectResponse("/placement-test/result", status_code=status.HTTP_302_FOUND)

    return render_template(
        request,
        "placement/question.html",
        {
            "question": q,
            "index": idx + 1,
            "total": len(questions),
            "age": age,
            "is_kid": age is not None and age <= 15,
            "error": None,
        },
    )


@router.post("/placement-test")
async def placement_submit(request: Request, db: Session = Depends(get_db)):
    user = _load_user(request, db)
    age = user.age if user else None

    run = request.session.get("placement_run") or {}
    questions = _build_questions(age)
    idx = int(run.get("idx") or 0)
    answers = run.get("answers") or []

    form = await request.form()
    raw_val = form.get("answer")
    if raw_val is None:
        q = questions[idx] if idx < len(questions) else None
        return render_template(
            request,
            "placement/question.html",
            {
                "question": q,
                "index": idx + 1,
                "total": len(questions),
                "age": age,
                "is_kid": age is not None and age <= 15,
                "error": "Пожалуйста, выберите вариант перед продолжением.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        selected = int(raw_val)
    except ValueError:
        selected = None

    if selected is None or idx >= len(questions):
        return RedirectResponse("/placement-test", status_code=status.HTTP_302_FOUND)

    q = questions[idx]
    is_correct = selected == q["correct"]
    answers.append({"id": q["id"], "selected": selected, "correct": q["correct"], "is_correct": is_correct})
    idx += 1

    # if finished
    if idx >= len(questions):
        score = sum(1 for a in answers if a["is_correct"])
        total_questions = len(questions)
        normalized_score = level_score(score, total_questions)
        level = compute_level(score, total_questions)
        result_payload = {
            "score": normalized_score,
            "total": total_questions,
            "raw_score": score,
            "level": level,
        }
        request.session["placement_result"] = result_payload
        request.session.pop("placement_run", None)

        record = models.PlacementTestResult(
            user_id=user.id if user else None,
            level=level,
            score=normalized_score,
            answers={"questions": answers, "total": total_questions, "raw_score": score},
        )
        db.add(record)
        if user:
            user.level = level
            db.add(user)
        db.commit()

        return RedirectResponse("/placement-test/result", status_code=status.HTTP_302_FOUND)

    # continue to next question
    run = {"idx": idx, "answers": answers}
    request.session["placement_run"] = run
    next_q = questions[idx]
    return render_template(
        request,
        "placement/question.html",
        {
            "question": next_q,
            "index": idx + 1,
            "total": len(questions),
            "age": age,
            "is_kid": age is not None and age <= 15,
            "error": None,
        },
    )


def level_score(score: int, total_questions: int) -> int:
    from math import ceil

    if total_questions == 0:
        return 0
    if total_questions == 20:
        return score
    return ceil(score * 20 / total_questions)


@router.get("/placement-test/result")
async def placement_result(request: Request, db: Session = Depends(get_db)):
    result = request.session.get("placement_result")
    if not result:
        return RedirectResponse("/placement-test", status_code=status.HTTP_302_FOUND)

    user = _load_user(request, db)
    age = user.age if user else None
    target = user.target if user else None

    recommended_slug = recommend_course_slug(age, target)
    course = db.query(models.Course).filter_by(slug=recommended_slug).first()

    first_lesson = (
        db.query(models.Lesson)
        .join(models.Module, models.Module.id == models.Lesson.module_id)
        .filter(models.Module.course_id == (course.id if course else None))
        .order_by(models.Module.order, models.Lesson.order)
        .first()
        if course
        else None
    )

    start_url = f"/lesson/{first_lesson.id}" if first_lesson else (f"/course/{course.slug}" if course else "/courses")

    return render_template(
        request,
        "placement_result.html",
        {
            "level": result["level"],
            "score": result["score"],
            "total": result["total"],
            "description": LEVEL_DESCRIPTIONS.get(result["level"], ""),
            "course": course,
            "start_url": start_url,
        },
    )
