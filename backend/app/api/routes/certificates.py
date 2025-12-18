from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...core.config import get_settings
from ...db import models
from ...services.progress_service import calculate_course_progress

router = APIRouter(prefix="/api/certificates", tags=["certificates"])
# Default fallbacks if course-specific mapping is not found
DEFAULT_CERTIFICATE = "certificates/qazaq-certificate.pdf"
COURSE_CERTIFICATES = {
    "kazpro": "certificates/qazaq-certificate.pdf",
    "kazkids": "certificates/qazaq-certificate.png",
    "qazaqmentor": "certificates/qazaq-certificate.pdf",
}


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


@router.get("/my")
def my_certificate(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    settings = get_settings()
    courses = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .all()
    )

    certificate_ready = False
    selected_slug: str | None = None
    for course in courses:
        percent, _, progress_map = calculate_course_progress(db, user, course)
        if percent >= 100 or (progress_map and all(status == "done" for status in progress_map.values())):
            certificate_ready = True
            selected_slug = getattr(course, "slug", None)
            break

    if not certificate_ready:
        return {"available": False}

    # Pick certificate file by course slug
    relative_path = DEFAULT_CERTIFICATE
    if selected_slug:
        slug_key = str(selected_slug).lower()
        # Accept aliases for mentor/pro course
        if slug_key in {"kazmentor", "qazaqmentor"}:
            slug_key = "kazpro"
        relative_path = COURSE_CERTIFICATES.get(slug_key, DEFAULT_CERTIFICATE)

    base_url = settings.cdn_base_url or "/uploads"
    url = f"{base_url.rstrip('/')}/{relative_path}"

    # Ensure file exists to avoid broken links
    uploads_root = Path(settings.upload_root or ".")
    cert_path = uploads_root / relative_path
    if not cert_path.exists():
        return {"available": False}

    return {"available": True, "url": url}
