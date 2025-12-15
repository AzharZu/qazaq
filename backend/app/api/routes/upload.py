from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ...api import deps
from ...services.storage_service import (
    generate_video_thumbnail,
    store_upload,
    validate_audio_file,
)
from ...core.config import get_settings
from uuid import uuid4
import os

router = APIRouter(prefix="/api/upload", tags=["upload"])
admin_router = APIRouter(prefix="/api/admin/upload", tags=["admin-upload"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...), user=Depends(deps.require_admin)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported image type")
    data = await file.read()
    stored = store_upload("image", file, data)
    return {"url": stored["url"], "filename": stored["filename"]}


@router.post("/audio")
async def upload_audio(file: UploadFile = File(...), user=Depends(deps.require_admin)):
    validate_audio_file(file)
    data = await file.read()
    stored = store_upload("audio", file, data)
    return {"url": stored["url"], "filename": stored["filename"]}


@router.post("/video")
async def upload_video(file: UploadFile = File(...), user=Depends(deps.require_admin)):
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported video type")
    data = await file.read()
    stored = store_upload("video", file, data)
    thumb_url = generate_video_thumbnail(Path(stored["path"]))
    return {"url": stored["url"], "filename": stored["filename"], "thumbnail_url": thumb_url}


@admin_router.post("")
async def admin_upload(file: UploadFile = File(...), user=Depends(deps.require_admin)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")
    settings = get_settings()
    ext = Path(file.filename).suffix or ""
    safe_ext = ext if ext.startswith(".") else f".{ext}" if ext else ""
    target_name = f"{uuid4().hex}{safe_ext}"
    target_dir = Path(settings.upload_root or "/app/uploads")
    target_dir.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    target_path = target_dir / target_name
    with open(target_path, "wb") as fh:
        fh.write(data)
    url = f"/uploads/{target_name}"
    return {"url": url}
