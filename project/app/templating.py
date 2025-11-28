from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_template(
    request: Request,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
) -> Response:
    ctx: Dict[str, Any] = {"request": request, "user": getattr(request.state, "user", None)}
    if context:
        ctx.update(context)

    if status_code is not None:
        return templates.TemplateResponse(template_name, ctx, status_code=status_code)
    return templates.TemplateResponse(template_name, ctx)
