from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.course import CourseOut, CourseWithProgress, CourseCreate, CourseUpdate
from ...services.progress_service import (
    calculate_course_progress,
    list_courses_with_progress,
    serialize_course,
    serialize_lesson,
)
from ...utils.encoding_fix import clean_encoding

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=dict)
def list_courses(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_current_user(request, db=db, allow_anonymous=True)
    entries = list_courses_with_progress(db, user)
    payload: list[dict] = []
    for entry in entries:
        course = entry["course"]
        if course.slug == "system-unassigned":
            continue
        data = serialize_course(course)
        data["progress_percent"] = entry["progress_percent"]
        data["next_lesson"] = serialize_lesson(entry["next_lesson"]) if entry["next_lesson"] else None
        data["progress_map"] = entry.get("progress_map", {})
        payload.append(data)
    return {"courses": payload}


@router.get("/{course_id:int}", response_model=CourseWithProgress)
def course_detail_by_id(course_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_current_user(request, db=db, allow_anonymous=True)
    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .filter(models.Course.id == course_id)
        .first()
    )
    if not course or course.slug == "system-unassigned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    progress_percent, next_lesson, progress_map = calculate_course_progress(db, user, course)
    payload = serialize_course(course)
    payload["progress_percent"] = progress_percent
    payload["next_lesson"] = serialize_lesson(next_lesson) if next_lesson else None
    payload["progress_map"] = progress_map
    return payload


@router.get("/id/{course_id}", response_model=CourseWithProgress)
def course_detail_by_id_alias(course_id: int, request: Request, db: Session = Depends(deps.current_db)):
    return course_detail_by_id(course_id, request, db)


@router.get("/{slug}", response_model=CourseWithProgress)
def course_detail(slug: str, request: Request, db: Session = Depends(deps.current_db)):
    if slug == "system-unassigned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    user = deps.get_current_user(request, db=db, allow_anonymous=True)
    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .filter(models.Course.slug == slug)
        .first()
    )
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    progress_percent, next_lesson, progress_map = calculate_course_progress(db, user, course)
    payload = serialize_course(course)
    payload["progress_percent"] = progress_percent
    payload["next_lesson"] = serialize_lesson(next_lesson) if next_lesson else None
    payload["progress_map"] = progress_map
    return payload


@router.get("/id/{course_id}/progress")
def course_progress(course_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
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
    percent = int((done / total) * 100)
    return {"percent": percent}


# Alias for /api/course/{id}/progress
@router.get("/course/{course_id}/progress")
def course_progress_alias(course_id: int, request: Request, db: Session = Depends(deps.current_db)):
    return course_progress(course_id, request, db)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    existing = db.query(models.Course).filter(models.Course.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course with this slug already exists")
    course = models.Course(
        slug=clean_encoding(payload.slug.strip()),
        name=clean_encoding(payload.name.strip()),
        description=clean_encoding(payload.description.strip()),
        audience=clean_encoding(payload.audience.strip()),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return serialize_course(course)


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    course = db.get(models.Course, course_id)
    if not course or course.slug == "system-unassigned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if payload.slug and payload.slug != course.slug:
        conflict = db.query(models.Course).filter(models.Course.slug == payload.slug).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course with this slug already exists")
        course.slug = clean_encoding(payload.slug.strip())
    if payload.name is not None:
        course.name = clean_encoding(payload.name.strip())
    if payload.description is not None:
        course.description = clean_encoding(payload.description.strip())
    if payload.audience is not None:
        course.audience = clean_encoding(payload.audience.strip())
    db.add(course)
    db.commit()
    db.refresh(course)
    return serialize_course(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    course = db.get(models.Course, course_id)
    if not course or course.slug == "system-unassigned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    db.delete(course)
    db.commit()
    return None
