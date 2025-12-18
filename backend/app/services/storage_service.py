from __future__ import annotations

import mimetypes
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from ..core.config import get_settings


ALLOWED_AUDIO_MIMES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/aac",
}


def sanitize_filename(name: str) -> str:
    name = name or "upload"
    name = re.sub(r"[^\w.-]+", "_", name, flags=re.UNICODE)
    return name.strip("._") or "upload"


def _target_paths(kind: str, filename: str) -> Tuple[Path, str]:
    settings = get_settings()
    root = Path(settings.upload_root)
    target_dir = root / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    url = f"{settings.cdn_base_url.rstrip('/')}/{kind}/{filename}"
    return target_dir / filename, url


def _write_file(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as f:
        f.write(data)


def validate_audio_file(file: UploadFile, size_bytes: int | None = None, max_mb: int = 15) -> None:
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime and mime.lower() not in ALLOWED_AUDIO_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format {mime}",
        )
    if size_bytes is not None and size_bytes > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file is too large (>{max_mb}MB)",
        )


def store_upload(kind: str, upload: UploadFile, data: bytes) -> dict:
    ext = Path(upload.filename or "").suffix or mimetypes.guess_extension(upload.content_type or "") or ".bin"
    base = sanitize_filename(Path(upload.filename or "upload").stem)
    filename = f"{base}_{uuid4().hex[:8]}{ext}"
    target_path, url = _target_paths(kind, filename)
    _write_file(target_path, data)
    return {"path": str(target_path), "url": url, "filename": filename}


def generate_video_thumbnail(video_path: Path) -> str | None:
    ffmpeg = os.environ.get("FFMPEG_BIN") or "ffmpeg"
    if not shutil.which(ffmpeg):
        return None
    thumb_name = f"{video_path.stem}_thumb.jpg"
    thumb_path = video_path.parent / thumb_name
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-ss",
                "00:00:00.5",
                "-vframes",
                "1",
                str(thumb_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    settings = get_settings()
    url = f"{settings.cdn_base_url.rstrip('/')}/video/{thumb_path.name}"
    return url
