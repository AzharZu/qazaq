from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.course import CourseCreate, CourseUpdate, CourseOut
from ...services.progress_service import serialize_module
from ...utils.encoding_fix import clean_encoding


router = APIRouter(prefix="/api/admin/courses", tags=["admin-courses"])


def _serialize_admin_course(course: models.Course) -> dict:
    modules = sorted(course.modules, key=lambda m: m.order)
    return {
        "id": course.id,
        "slug": course.slug,
        "name": clean_encoding(course.name),
        "description": clean_encoding(course.description),
        "audience": course.audience,
        "modules": [serialize_module(m, include_unpublished=True) for m in modules],
    }


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    courses = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .all()
    )
    return [_serialize_admin_course(course) for course in courses]


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
    return _serialize_admin_course(course)


@router.patch("/{course_id}", response_model=CourseOut)
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
    return _serialize_admin_course(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    course = db.get(models.Course, course_id)
    if not course or course.slug == "system-unassigned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    db.delete(course)
    db.commit()
    return None
