from fastapi import APIRouter, Depends, Form, Request, status

from .. import models
from ..dependencies import get_current_user
from ..services import analyze_text, AutoCheckerError
from ..templating import render_template

router = APIRouter(tags=["autochecker"])


def _mentor_tip(grammar: int, vocabulary: int) -> str:
    g = int(grammar or 0)
    v = int(vocabulary or 0)
    if g >= 8 and v >= 8:
        return "Жардайсың! Только шлифуй детали."
    if g >= 5 and v >= 5:
        return "Неплохо, но есть над чем поработать."
    return "Это хороший старт. Давай вместе подтянем базу."


@router.get("/autochecker")
async def autochecker_page(request: Request, user: models.User = Depends(get_current_user)):
    return render_template(
        request,
        "autochecker.html",
        {"result": None, "error": None, "input_text": "", "level": "A2", "mentor_tip": None, "user": user},
    )


@router.post("/autochecker")
async def autochecker_submit(
    request: Request,
    user_text: str = Form(""),
    level: str = Form("A2"),
    user: models.User = Depends(get_current_user),
):
    text = (user_text or "").strip()
    selected_level = (level or "A2").upper()
    if not text:
        return render_template(
            request,
            "autochecker.html",
            {
                "result": None,
                "error": "Введите текст!",
                "input_text": "",
                "level": selected_level,
                "mentor_tip": None,
                "user": user,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = await analyze_text(text, selected_level)
        error = None
        status_code = status.HTTP_200_OK
        mentor_tip = _mentor_tip(result.get("grammar_score"), result.get("vocabulary_score"))
    except AutoCheckerError as exc:
        result = None
        error = str(exc) or "Сейчас не удалось проанализировать текст, попробуйте позже."
        status_code = status.HTTP_502_BAD_GATEWAY
        mentor_tip = None
    except Exception:
        result = None
        error = "Сейчас не удалось проанализировать текст, попробуйте позже."
        status_code = status.HTTP_502_BAD_GATEWAY
        mentor_tip = None

    return render_template(
        request,
        "autochecker.html",
        {
            "result": result,
            "error": error,
            "input_text": text,
            "level": selected_level,
            "mentor_tip": mentor_tip,
            "user": user,
        },
        status_code=status_code,
    )
