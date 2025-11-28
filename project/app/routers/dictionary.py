from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..services.dictionary import get_user_dictionary_grouped
from ..templating import render_template

router = APIRouter(tags=["dictionary"])


@router.get("/dictionary")
async def dictionary_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    grouped = get_user_dictionary_grouped(user.id, db)
    return render_template(request, "dictionary.html", {"grouped": grouped, "user": user})


@router.post("/dictionary/delete/{entry_id}")
async def dictionary_delete(entry_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    entry = (
        db.query(models.UserDictionary)
        .filter(models.UserDictionary.id == entry_id, models.UserDictionary.user_id == user.id)
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
    return RedirectResponse("/dictionary", status_code=status.HTTP_302_FOUND)
