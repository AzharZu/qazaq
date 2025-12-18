from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.level_test import LevelTestAnswer, LevelTestQuestionOut, LevelTestResult
from ...services.progress_service import recommend_course_slug

router = APIRouter(prefix="/api/level-test", tags=["level-test"])


def _serialize_question(q: models.LevelTestQuestion) -> LevelTestQuestionOut:
    options = sorted(q.options or [], key=lambda o: o.order)
    return LevelTestQuestionOut(
        id=q.id,
        text=q.text,
        example=q.example,
        correct_index=q.correct_index,
        options=[{"id": opt.id, "text": opt.text, "order": opt.order} for opt in options],
    )


@router.get("/questions", response_model=list[LevelTestQuestionOut])
def level_test_questions(db: Session = Depends(deps.current_db)):
    questions = (
        db.query(models.LevelTestQuestion)
        .options(selectinload(models.LevelTestQuestion.options))
        .order_by(models.LevelTestQuestion.id)
        .all()
    )
    return [_serialize_question(q) for q in questions]


@router.post("/result", response_model=LevelTestResult)
def level_test_result(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    answers_raw = payload.get("answers") or []
    answers = []
    try:
        answers = [LevelTestAnswer(**a) for a in answers_raw]
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid answers payload")

    questions = (
        db.query(models.LevelTestQuestion)
        .options(selectinload(models.LevelTestQuestion.options))
        .all()
    )
    q_map = {q.id: q for q in questions}
    correct = 0
    total = len(questions) or 1
    for ans in answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue
        if ans.selected == q.correct_index:
            correct += 1
    ratio = correct / total
    level = "A0"
    if ratio >= 0.85:
        level = "B2"
    elif ratio >= 0.7:
        level = "B1"
    elif ratio >= 0.5:
        level = "A2"
    elif ratio >= 0.25:
        level = "A1"
    user = getattr(request.state, "user", None)
    age = user.age if user else None
    target = user.target if user else None
    recommended_slug = recommend_course_slug(age, target, level)
    course = (
        db.query(models.Course)
        .filter(models.Course.slug == recommended_slug)
        .first()
    )
    course_payload = None
    if course:
        course_payload = {
            "id": course.id,
            "slug": course.slug,
            "name": course.name,
            "description": course.description,
            "audience": course.audience,
        }
    if user:
        user.level = level
        db.add(user)
        db.commit()
    return LevelTestResult(
        level=level,
        recommended_course=recommended_slug,
        score=correct,
        total=total,
        course=course_payload,
    )
