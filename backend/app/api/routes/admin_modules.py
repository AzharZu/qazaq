from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.module import ModuleCreate, ModuleUpdate, ModuleOut
from ...services.progress_service import serialize_module
from ...utils.encoding_fix import clean_encoding


router = APIRouter(prefix="/api/admin/modules", tags=["admin-modules"])


@router.get("", response_model=list[ModuleOut])
def list_modules(course_id: Optional[int] = None, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    query = db.query(models.Module).options(selectinload(models.Module.lessons))
    if course_id is not None:
        course = db.get(models.Course, course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        query = query.filter(models.Module.course_id == course_id)
    modules = sorted(query.all(), key=lambda m: m.order)
    return [serialize_module(m, include_unpublished=True) for m in modules]


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


@router.patch("/{module_id}", response_model=ModuleOut)
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
