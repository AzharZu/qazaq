from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


@router.get("")
def list_certificates(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    rows = (
        db.query(models.Certificate)
        .filter(models.Certificate.user_id == user.id)
        .order_by(models.Certificate.created_at.desc())
        .all()
    )
    return [{"id": r.id, "course_id": r.course_id, "url": r.url, "created_at": r.created_at} for r in rows]


@router.post("/generate")
def generate_certificate(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    course_id = payload.get("course_id")
    if not course_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course_id is required")
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    # Compute completion
    lessons = [l for m in course.modules for l in m.lessons if not getattr(l, "is_deleted", False)]
    total = len(lessons) or 1
    done = (
        db.query(models.UserLessonProgress)
        .filter(
            models.UserLessonProgress.user_id == user.id,
            models.UserLessonProgress.lesson_id.in_([l.id for l in lessons]),
            models.UserLessonProgress.status == "finished",
        )
        .count()
    )
    if done < total:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course not completed")
    url = f"/static/certificates/{user.id}_{course.id}.pdf"
    cert = models.Certificate(user_id=user.id, course_id=course.id, url=url)
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return {"url": cert.url}
