from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models
from ...schemas.placement import (
    PlacementAnswerPayload,
    PlacementFinishPayload,
    PlacementQuestionsResponse,
    PlacementResult,
)
from ...services.placement_service import (
    answer_question,
    next_question,
    score_answers,
    select_questions,
    start_run,
)
from ...services.progress_service import recommend_course_slug

router = APIRouter(prefix="/api/placement", tags=["placement"])


@router.get("/questions", response_model=PlacementQuestionsResponse)
def placement_questions(request: Request, limit: int = 20, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None
    normalized_limit = max(1, min(int(limit or 20), 50))
    questions = select_questions(age, normalized_limit)
    request.session["placement_questions"] = [q["id"] for q in questions]
    request.session["placement_answers"] = []
    return PlacementQuestionsResponse(questions=questions, total=len(questions))


@router.get("/start")
@router.post("/start")
def placement_start(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None
    return start_run(request.session, age)


@router.get("/next")
@router.post("/next")
def placement_next(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None
    return next_question(request.session, age)


@router.post("/answer")
def placement_answer(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    """
    Compatibility endpoint: logs answer during the run and also supports
    the new payload {question_id, selected_option} for analytics.
    """
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None

    # New-style payload: persist answers in the session for finish()
    if "question_id" in payload and "selected_option" in payload:
        try:
            normalized = PlacementAnswerPayload(
                question_id=str(payload.get("question_id")),
                selected_option=int(payload.get("selected_option")),
            )
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid answer payload")
        answers = request.session.get("placement_answers") or []
        answers = [a for a in answers if a.get("question_id") != normalized.question_id]
        answers.append(normalized.model_dump())
        request.session["placement_answers"] = answers
        return {"saved": True, "total_answered": len(answers)}

    # Legacy flow: keep old navigation-based behaviour
    result = answer_question(payload, request.session, user, db, age)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/result")
def placement_result(request: Request, db: Session = Depends(deps.current_db)):
    result = request.session.get("placement_result")
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement not finished")
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None
    target = user.target if user else None
    result_level = None
    try:
        result_level = result.get("level")
    except Exception:
        result_level = None
    recommended_slug = recommend_course_slug(age, target, result_level)
    result = dict(result)
    result["recommended_course"] = recommended_slug
    request.session["placement_result"] = result
    request.session["recommended_course_slug"] = recommended_slug
    course = (
        db.query(models.Course)
        .filter(models.Course.slug == recommended_slug)
        .first()
    )
    return {
        **result,
        "course": {
            "id": course.id,
            "slug": course.slug,
            "name": course.name,
            "description": course.description,
            "audience": course.audience,
        }
        if course
        else None,
    }


@router.post("/finish", response_model=PlacementResult)
def placement_finish(payload: PlacementFinishPayload, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    age = user.age if user else None
    target = user.target if user else None
    limit = max(1, min(payload.limit or 20, 50))

    session_ids = request.session.get("placement_questions") or []
    answers = [ans.model_dump() for ans in payload.answers]
    computed = score_answers(answers, age, session_question_ids=session_ids)

    # Normalize totals to the requested limit for consistency
    computed["total"] = min(computed.get("total") or limit, limit)

    recommended_slug = recommend_course_slug(age, target, computed.get("level"))
    result_payload = {
        "level": computed["level"],
        "recommended_course": recommended_slug,
        "score": computed["score"],
        "total": computed["total"],
        "raw_score": computed["raw_score"],
    }
    request.session["placement_result"] = result_payload
    request.session["recommended_course_slug"] = recommended_slug
    if user:
        db.add(
            models.PlacementTestResult(
                user_id=user.id,
                level=computed["level"],
                score=computed["score"],
                answers={
                    "questions": computed["answers"],
                    "total": computed["total"],
                    "raw_score": computed["raw_score"],
                },
            )
        )
        user.level = computed["level"]
        db.add(user)
        db.commit()
    return result_payload
