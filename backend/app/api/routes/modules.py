from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.module import ModuleCreate, ModuleUpdate, ModuleOut
from ...services.progress_service import module_with_progress, serialize_lesson, serialize_module
from ...utils.encoding_fix import clean_encoding

router = APIRouter(prefix="/api/modules", tags=["modules"])


@router.get("")
def modules_by_course(
    request: Request,
    course_id: Optional[int] = None,
    course_slug: Optional[str] = None,
    db: Session = Depends(deps.current_db),
):
    user = deps.get_user_or_none(request, db=db)
    include_unpublished = bool(user and getattr(user, "is_admin", False))
    # Admin/list-all fallback: no filters -> return all modules
    if course_id is None and course_slug is None:
        modules = db.query(models.Module).options(selectinload(models.Module.lessons)).all()
        return [serialize_module(m, include_unpublished=include_unpublished) | {"progress_map": {}} for m in modules]

    course = None
    if course_id:
        course = db.get(models.Course, course_id)
    if not course and course_slug:
        course = (
            db.query(models.Course)
            .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
            .filter(models.Course.slug == course_slug)
            .first()
        )
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    lesson_ids = [lesson.id for m in course.modules for lesson in m.lessons]
    progress_map = {}
    if lesson_ids and user:
        rows = (
            db.query(models.UserProgress)
            .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id.in_(lesson_ids))
            .all()
        )
        progress_map = {row.lesson_id: row.status for row in rows}
    modules = sorted(course.modules, key=lambda m: m.order)
    return [serialize_module(m, include_unpublished=include_unpublished) | {"progress_map": progress_map} for m in modules]


@router.get("/{module_id}")
def module_detail(module_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    include_unpublished = bool(user and getattr(user, "is_admin", False))
    module, progress_map = module_with_progress(db, module_id, user)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    payload = serialize_module(module, include_unpublished=include_unpublished)
    payload["progress_map"] = progress_map
    return payload


@router.get("/{module_id}/lessons")
def module_lessons(module_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    include_unpublished = bool(user and getattr(user, "is_admin", False))
    module, progress_map = module_with_progress(db, module_id, user)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    lessons = [
        l
        for l in module.lessons
        if not getattr(l, "is_deleted", False)
        and getattr(l, "status", "draft") != "archived"
        and (include_unpublished or getattr(l, "status", "draft") == "published")
    ]
    return {
        "lessons": [serialize_lesson(l) for l in lessons],
        "progress_map": progress_map,
    }


@router.post("", response_model=ModuleOut, status_code=status.HTTP_201_CREATED)
def create_module(payload: ModuleCreate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    course = db.get(models.Course, payload.course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    order = payload.order or (len(course.modules) + 1)
    module = models.Module(
        course_id=payload.course_id,
        name=clean_encoding(payload.name.strip()),
        order=order,
        description=clean_encoding(payload.description) if payload.description else None,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return serialize_module(module, include_unpublished=True)


@router.put("/{module_id}", response_model=ModuleOut)
def update_module(
    module_id: int,
    payload: ModuleUpdate,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if payload.course_id:
        course = db.get(models.Course, payload.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        module.course_id = payload.course_id
    if payload.name is not None:
        module.name = clean_encoding(payload.name.strip())
    if payload.description is not None:
        module.description = clean_encoding(payload.description) if payload.description else None
    if payload.order is not None:
        module.order = payload.order
    db.add(module)
    db.commit()
    db.refresh(module)
    return serialize_module(module, include_unpublished=True)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(module_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    db.delete(module)
    db.commit()
    return None
