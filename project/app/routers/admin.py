from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..dependencies import require_admin
from ..templating import render_template

router = APIRouter(dependencies=[Depends(require_admin)])

BLOCK_TYPES = [
    "theory",
    "example",
    "mascot_tip",
    "flashcards",
    "quiz",
    "pronunciation",
    "dragdrop",
    "story",
]


def _build_theory(data: dict) -> dict:
    return {"title": data.get("title"), "text": data.get("text")}


def _build_example(data: dict) -> dict:
    examples = []
    for i in range(1, 4):
        kz = data.get(f"example_{i}_kz")
        ru = data.get(f"example_{i}_ru")
        if kz or ru:
            examples.append({"kz": kz or "", "ru": ru or ""})
    return {"examples": examples}


def _build_mascot(data: dict) -> dict:
    return {"text": data.get("text"), "icon": data.get("icon") or "🦊"}


def _build_flashcards(data: dict) -> dict:
    ids = data.get("selected_flashcard_ids", [])
    return {"flashcard_ids": [int(x) for x in ids]}


def _build_quiz(data: dict) -> dict:
    ids = data.get("selected_quiz_ids", [])
    return {"quiz_ids": [int(x) for x in ids]}


def _build_pronunciation(data: dict) -> dict:
    words_raw = data.get("words") or ""
    words = [w.strip() for w in words_raw.splitlines() if w.strip()]
    return {"words": words}


def _build_dragdrop(data: dict) -> dict:
    parts = [p.strip() for p in (data.get("parts") or "").splitlines() if p.strip()]
    correct = [p.strip() for p in (data.get("correct_order") or "").splitlines() if p.strip()]
    return {"task": data.get("task"), "parts": parts, "correct_order": correct}


def _build_story(data: dict) -> dict:
    return {
        "situation": data.get("situation"),
        "question": data.get("question"),
        "options": [
            data.get("option_1"),
            data.get("option_2"),
            data.get("option_3"),
        ],
        "correct_index": int(data.get("correct_index") or 0),
    }


BLOCK_BUILDERS = {
    "theory": _build_theory,
    "example": _build_example,
    "mascot_tip": _build_mascot,
    "flashcards": _build_flashcards,
    "quiz": _build_quiz,
    "pronunciation": _build_pronunciation,
    "dragdrop": _build_dragdrop,
    "story": _build_story,
}


def _to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def build_block_content(block_type: str, form_data: dict) -> dict:
    builder = BLOCK_BUILDERS.get(block_type)
    if builder:
        return builder(form_data)
    return form_data


def _normalize_orders(db: Session, lesson_id: int) -> None:
    blocks = (
        db.query(models.LessonBlock)
        .filter(models.LessonBlock.lesson_id == lesson_id)
        .order_by(models.LessonBlock.order, models.LessonBlock.id)
        .all()
    )
    for idx, block in enumerate(blocks, start=1):
        if block.order != idx:
            block.order = idx
            db.add(block)
    db.commit()


def _clamp_order(desired: Optional[int], min_value: int, max_value: int) -> int:
    if desired is None:
        return max_value
    return max(min_value, min(desired, max_value))


def _insert_block_with_order(db: Session, block: models.LessonBlock, desired_order: Optional[int]) -> None:
    existing_blocks = (
        db.query(models.LessonBlock)
        .filter(models.LessonBlock.lesson_id == block.lesson_id)
        .order_by(models.LessonBlock.order)
        .all()
    )
    max_order = len(existing_blocks) + 1
    target_order = _clamp_order(desired_order, 1, max_order)
    for existing in existing_blocks:
        if existing.order >= target_order:
            existing.order += 1
            db.add(existing)
    block.order = target_order
    db.add(block)
    db.commit()
    _normalize_orders(db, block.lesson_id)


def _update_block_order(db: Session, block: models.LessonBlock, new_order: Optional[int]) -> None:
    blocks = (
        db.query(models.LessonBlock)
        .filter(models.LessonBlock.lesson_id == block.lesson_id)
        .order_by(models.LessonBlock.order, models.LessonBlock.id)
        .all()
    )
    max_order = len(blocks)
    target_order = _clamp_order(new_order, 1, max_order)
    if target_order == block.order:
        return

    for b in blocks:
        if b.id == block.id:
            continue
        if target_order < block.order and target_order <= b.order < block.order:
            b.order += 1
            db.add(b)
        elif target_order > block.order and block.order < b.order <= target_order:
            b.order -= 1
            db.add(b)

    block.order = target_order
    db.add(block)
    db.commit()
    _normalize_orders(db, block.lesson_id)


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


def _breadcrumbs_root() -> list[dict[str, str]]:
    return [{"label": "Админ", "url": "/admin"}]


def _breadcrumbs_for_course(course: models.Course | None) -> list[dict[str, str]]:
    crumbs = _breadcrumbs_root()
    crumbs.append({"label": "Курсы", "url": "/admin/courses"})
    if course:
        crumbs.append({"label": course.name, "url": f"/admin/course/{course.id}/modules"})
    return crumbs


def _breadcrumbs_for_module(module: models.Module | None) -> list[dict[str, str]]:
    course = module.course if module else None
    crumbs = _breadcrumbs_for_course(course)
    if module:
        crumbs.append({"label": f'Модуль "{module.name}"', "url": f"/admin/module/{module.id}/lessons"})
    return crumbs


def _breadcrumbs_for_lesson(lesson: models.Lesson | None) -> list[dict[str, str]]:
    module = lesson.module if lesson else None
    crumbs = _breadcrumbs_for_module(module)
    if lesson:
        crumbs.append({"label": f'Урок "{lesson.title}"', "url": f"/admin/lesson/{lesson.id}"})
    return crumbs


@router.get("/")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    data = {
        "courses": db.query(models.Course).count(),
        "modules": db.query(models.Module).count(),
        "lessons": db.query(models.Lesson).count(),
        "blocks": db.query(models.LessonBlock).count(),
        "flashcards": db.query(models.Flashcard).count(),
        "quizzes": db.query(models.Quiz).count(),
    }
    return render_template(request, "admin/dashboard.html", {**data, "breadcrumbs": _breadcrumbs_root()})


@router.get("/courses")
async def admin_courses(request: Request, db: Session = Depends(get_db)):
    courses = db.query(models.Course).all()
    breadcrumbs = _breadcrumbs_for_course(None)
    return render_template(request, "admin/courses.html", {"courses": courses, "breadcrumbs": breadcrumbs})


@router.get("/course/{course_id}/edit")
async def admin_edit_course(course_id: int, request: Request, db: Session = Depends(get_db)):
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    breadcrumbs = _breadcrumbs_for_course(course) + [{"label": "Редактировать курс"}]
    return render_template(request, "admin/edit_course.html", {"course": course, "breadcrumbs": breadcrumbs})


@router.post("/course/{course_id}/edit")
async def admin_update_course(
    course_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    audience: str = Form(...),
    db: Session = Depends(get_db),
):
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.name = name
    course.description = description
    course.audience = audience
    db.add(course)
    db.commit()
    return _redirect(f"/admin/courses")


@router.get("/course/{course_id}/modules")
async def admin_course_modules(course_id: int, request: Request, db: Session = Depends(get_db)):
    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .filter(models.Course.id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    breadcrumbs = _breadcrumbs_for_course(course)
    return render_template(request, "admin/modules.html", {"course": course, "breadcrumbs": breadcrumbs})


@router.get("/module/{module_id}/edit")
async def admin_edit_module(module_id: int, request: Request, db: Session = Depends(get_db)):
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    breadcrumbs = _breadcrumbs_for_module(module) + [{"label": "Редактировать модуль"}]
    return render_template(request, "admin/edit_module.html", {"module": module, "breadcrumbs": breadcrumbs})


@router.post("/module/{module_id}/edit")
async def admin_update_module(
    module_id: int,
    request: Request,
    name: str = Form(...),
    order: int = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    module.name = name
    module.order = order
    module.description = description
    db.add(module)
    db.commit()
    return _redirect(f"/admin/course/{module.course_id}/modules")


@router.get("/module/{module_id}/lessons")
async def admin_module_lessons(module_id: int, request: Request, db: Session = Depends(get_db)):
    module = (
        db.query(models.Module)
        .options(selectinload(models.Module.lessons), selectinload(models.Module.course))
        .filter(models.Module.id == module_id)
        .first()
    )
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    breadcrumbs = _breadcrumbs_for_module(module) + [{"label": "Уроки"}]
    return render_template(request, "admin/lesson_list.html", {"module": module, "breadcrumbs": breadcrumbs})


@router.get("/lesson/{lesson_id}/edit")
async def admin_edit_lesson(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(selectinload(models.Lesson.module).selectinload(models.Module.course))
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    breadcrumbs = _breadcrumbs_for_lesson(lesson) + [{"label": "Редактировать урок"}]
    return render_template(request, "admin/edit_lesson.html", {"lesson": lesson, "breadcrumbs": breadcrumbs})


@router.post("/lesson/{lesson_id}/edit")
async def admin_update_lesson(
    lesson_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    lesson_type: str = Form(None),
    age_group: str = Form(None),
    estimated_time: Optional[int] = Form(None),
    difficulty: str = Form(None),
    order: int = Form(...),
    db: Session = Depends(get_db),
):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson.title = title
    lesson.description = description
    lesson.lesson_type = lesson_type
    lesson.age_group = age_group
    lesson.estimated_time = estimated_time
    lesson.difficulty = difficulty
    lesson.order = order
    db.add(lesson)
    db.commit()
    return _redirect(f"/admin/lesson/{lesson.id}")


@router.get("/lesson/{lesson_id}")
async def admin_lesson_detail(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.module).selectinload(models.Module.course),
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.quizzes),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    breadcrumbs = _breadcrumbs_for_lesson(lesson)
    flashcards_by_id = {card.id: card for card in lesson.flashcards}
    quizzes_by_id = {quiz.id: quiz for quiz in lesson.quizzes}
    return render_template(
        request,
        "admin/lesson_detail.html",
        {
            "lesson": lesson,
            "breadcrumbs": breadcrumbs,
            "flashcards_by_id": flashcards_by_id,
            "quizzes_by_id": quizzes_by_id,
        },
    )


@router.get("/lesson/{lesson_id}/blocks")
async def admin_lesson_blocks(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return _redirect(f"/admin/lesson/{lesson_id}")


def _extract_block_form_data(form) -> dict:
    return {
        "title": form.get("title"),
        "text": form.get("text"),
        "example_1_kz": form.get("example_1_kz"),
        "example_1_ru": form.get("example_1_ru"),
        "example_2_kz": form.get("example_2_kz"),
        "example_2_ru": form.get("example_2_ru"),
        "example_3_kz": form.get("example_3_kz"),
        "example_3_ru": form.get("example_3_ru"),
        "selected_flashcard_ids": form.getlist("selected_flashcard_ids") if hasattr(form, "getlist") else [],
        "selected_quiz_ids": form.getlist("selected_quiz_ids") if hasattr(form, "getlist") else [],
        "task": form.get("task"),
        "parts": form.get("parts"),
        "correct_order": form.get("correct_order"),
        "situation": form.get("situation"),
        "question": form.get("question"),
        "option_1": form.get("option_1"),
        "option_2": form.get("option_2"),
        "option_3": form.get("option_3"),
        "correct_index": form.get("correct_index"),
        "words": form.get("words"),
        "icon": form.get("icon"),
    }


@router.get("/lesson/{lesson_id}/blocks/add")
async def admin_add_block_form(
    lesson_id: int,
    request: Request,
    block_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.quizzes),
            selectinload(models.Lesson.module).selectinload(models.Module.course),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    selected_type = block_type if block_type in BLOCK_TYPES else None
    suggested_order = len(lesson.blocks) + 1
    breadcrumbs = _breadcrumbs_for_lesson(lesson) + [{"label": "Добавить блок"}]
    return render_template(
        request,
        "admin/add_block.html",
        {
            "lesson": lesson,
            "selected_type": selected_type,
            "block_types": BLOCK_TYPES,
            "suggested_order": suggested_order,
            "breadcrumbs": breadcrumbs,
        },
    )


@router.post("/lesson/{lesson_id}/blocks/add")
async def admin_add_block(
    lesson_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    block_type = form.get("block_type")
    if not block_type or block_type not in BLOCK_TYPES:
        raise HTTPException(status_code=400, detail="Invalid block type")

    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    order_raw = form.get("order")
    desired_order = _to_int(order_raw)
    form_data = _extract_block_form_data(form)
    content = build_block_content(block_type, form_data)
    block = models.LessonBlock(
        lesson_id=lesson_id,
        block_type=block_type,
        content=content,
        order=desired_order or 1,
    )
    _insert_block_with_order(db, block, desired_order)
    return _redirect(f"/admin/lesson/{lesson_id}")


@router.get("/block/{block_id}/edit")
async def admin_edit_block(
    block_id: int,
    request: Request,
    block_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    block = (
        db.query(models.LessonBlock)
        .options(
            selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.flashcards),
            selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.quizzes),
            selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.blocks),
            selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.module).selectinload(models.Module.course),
        )
        .filter(models.LessonBlock.id == block_id)
        .first()
    )
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    selected_type = block_type if block_type in BLOCK_TYPES else block.block_type
    suggested_order = len(block.lesson.blocks)
    breadcrumbs = _breadcrumbs_for_lesson(block.lesson) + [{"label": f"Блок #{block.id}"}]
    return render_template(
        request,
        "admin/edit_block.html",
        {
            "block": block,
            "lesson": block.lesson,
            "selected_type": selected_type,
            "block_types": BLOCK_TYPES,
            "suggested_order": suggested_order,
            "breadcrumbs": breadcrumbs,
        },
    )


@router.post("/block/{block_id}/edit")
async def admin_update_block(
    block_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    block = db.get(models.LessonBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    form = await request.form()
    block_type = form.get("block_type") or block.block_type
    if block_type not in BLOCK_TYPES:
        raise HTTPException(status_code=400, detail="Invalid block type")

    order_raw = form.get("order")
    desired_order = _to_int(order_raw) or block.order
    form_data = _extract_block_form_data(form)
    content = build_block_content(block_type, form_data)

    block.block_type = block_type
    block.content = content
    db.add(block)
    _update_block_order(db, block, desired_order)
    return _redirect(f"/admin/lesson/{block.lesson_id}")


@router.post("/block/{block_id}/delete")
async def admin_delete_block(block_id: int, db: Session = Depends(get_db)):
    block = db.get(models.LessonBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    lesson_id = block.lesson_id
    db.delete(block)
    db.commit()
    _normalize_orders(db, lesson_id)
    return _redirect(f"/admin/lesson/{lesson_id}")


@router.post("/block/{block_id}/move-up")
async def admin_move_block_up(block_id: int, db: Session = Depends(get_db)):
    block = db.get(models.LessonBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    _update_block_order(db, block, block.order - 1)
    return _redirect(f"/admin/lesson/{block.lesson_id}")


@router.post("/block/{block_id}/move-down")
async def admin_move_block_down(block_id: int, db: Session = Depends(get_db)):
    block = db.get(models.LessonBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    _update_block_order(db, block, block.order + 1)
    return _redirect(f"/admin/lesson/{block.lesson_id}")


@router.get("/lesson/{lesson_id}/flashcards")
async def admin_flashcards(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.module).selectinload(models.Module.course),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    breadcrumbs = _breadcrumbs_for_lesson(lesson) + [{"label": "Flashcards"}]
    return render_template(request, "admin/flashcards.html", {"lesson": lesson, "breadcrumbs": breadcrumbs})


@router.get("/flashcards/add")
async def admin_flashcard_add_form(lesson_id: int, request: Request):
    return render_template(request, "admin/edit_flashcard.html", {"flashcard": None, "lesson_id": lesson_id})


@router.post("/flashcards/add")
async def admin_flashcard_add(
    lesson_id: int,
    request: Request,
    front: str = Form(...),
    back: str = Form(...),
    image_url: Optional[str] = Form(None),
    audio_url: Optional[str] = Form(None),
    age_group: Optional[str] = Form(None),
    order: int = Form(1),
    db: Session = Depends(get_db),
):
    card = models.Flashcard(
        lesson_id=lesson_id,
        front=front,
        back=back,
        image_url=image_url,
        audio_url=audio_url,
        age_group=age_group,
        order=order,
    )
    db.add(card)
    db.commit()
    return _redirect(f"/admin/lesson/{lesson_id}/flashcards")


@router.get("/flashcard/{flashcard_id}/edit")
async def admin_flashcard_edit(flashcard_id: int, request: Request, db: Session = Depends(get_db)):
    card = db.get(models.Flashcard, flashcard_id)
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return render_template(request, "admin/edit_flashcard.html", {"flashcard": card, "lesson_id": card.lesson_id})


@router.post("/flashcard/{flashcard_id}/edit")
async def admin_flashcard_update(
    flashcard_id: int,
    request: Request,
    front: str = Form(...),
    back: str = Form(...),
    image_url: Optional[str] = Form(None),
    audio_url: Optional[str] = Form(None),
    age_group: Optional[str] = Form(None),
    order: int = Form(1),
    db: Session = Depends(get_db),
):
    card = db.get(models.Flashcard, flashcard_id)
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    card.front = front
    card.back = back
    card.image_url = image_url
    card.audio_url = audio_url
    card.age_group = age_group
    card.order = order
    db.add(card)
    db.commit()
    return _redirect(f"/admin/lesson/{card.lesson_id}/flashcards")


@router.get("/flashcard/{flashcard_id}/delete")
async def admin_flashcard_delete(flashcard_id: int, db: Session = Depends(get_db)):
    card = db.get(models.Flashcard, flashcard_id)
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    lesson_id = card.lesson_id
    db.delete(card)
    db.commit()
    return _redirect(f"/admin/lesson/{lesson_id}/flashcards")


@router.get("/lesson/{lesson_id}/quizzes")
async def admin_quizzes(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.quizzes),
            selectinload(models.Lesson.module).selectinload(models.Module.course),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    breadcrumbs = _breadcrumbs_for_lesson(lesson) + [{"label": "Quizzes"}]
    return render_template(request, "admin/quizzes.html", {"lesson": lesson, "breadcrumbs": breadcrumbs})


@router.get("/quizzes/add")
async def admin_quiz_add_form(lesson_id: int, request: Request):
    return render_template(request, "admin/edit_quiz.html", {"quiz": None, "lesson_id": lesson_id})


@router.post("/quizzes/add")
async def admin_quiz_add(
    lesson_id: int,
    request: Request,
    question: str = Form(...),
    option_1: str = Form(...),
    option_2: str = Form(...),
    option_3: str = Form(...),
    correct_option: int = Form(...),
    explanation: Optional[str] = Form(None),
    age_group: Optional[str] = Form(None),
    order: int = Form(1),
    db: Session = Depends(get_db),
):
    options = [option_1, option_2, option_3]
    quiz = models.Quiz(
        lesson_id=lesson_id,
        question=question,
        options=options,
        correct_option=correct_option,
        explanation=explanation,
        age_group=age_group,
        order=order,
    )
    db.add(quiz)
    db.commit()
    return _redirect(f"/admin/lesson/{lesson_id}/quizzes")


@router.get("/quiz/{quiz_id}/edit")
async def admin_quiz_edit(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    quiz = db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return render_template(request, "admin/edit_quiz.html", {"quiz": quiz, "lesson_id": quiz.lesson_id})


@router.post("/quiz/{quiz_id}/edit")
async def admin_quiz_update(
    quiz_id: int,
    request: Request,
    question: str = Form(...),
    option_1: str = Form(...),
    option_2: str = Form(...),
    option_3: str = Form(...),
    correct_option: int = Form(...),
    explanation: Optional[str] = Form(None),
    age_group: Optional[str] = Form(None),
    order: int = Form(1),
    db: Session = Depends(get_db),
):
    quiz = db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz.question = question
    quiz.options = [option_1, option_2, option_3]
    quiz.correct_option = correct_option
    quiz.explanation = explanation
    quiz.age_group = age_group
    quiz.order = order
    db.add(quiz)
    db.commit()
    return _redirect(f"/admin/lesson/{quiz.lesson_id}/quizzes")


@router.get("/quiz/{quiz_id}/delete")
async def admin_quiz_delete(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    lesson_id = quiz.lesson_id
    db.delete(quiz)
    db.commit()
    return _redirect(f"/admin/lesson/{lesson_id}/quizzes")
