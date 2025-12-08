from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(tags=["admin-spa"])

ADMIN_DIST = Path(__file__).resolve().parents[2] / "admin-spa" / "dist"
INDEX_HTML = ADMIN_DIST / "index.html"
VITE_SVG = ADMIN_DIST / "vite.svg"
assets_app = StaticFiles(directory=str(ADMIN_DIST / "assets"), check_dir=False)


def _index_response() -> FileResponse:
    if not INDEX_HTML.exists():
        raise HTTPException(
            status_code=503,
            detail="Admin SPA is not built yet. Run `npm run build` inside project/admin-spa.",
        )
    return FileResponse(INDEX_HTML)


@router.get("/admin/vite.svg", include_in_schema=False)
async def serve_vite_svg():
    if not VITE_SVG.exists():
        raise HTTPException(status_code=503, detail="Vite icon not found. Build admin-spa first.")
    return FileResponse(VITE_SVG, media_type="image/svg+xml")


@router.get("/admin", include_in_schema=False)
async def serve_admin_root():
    return _index_response()


@router.get("/admin/{full_path:path}", include_in_schema=False)
async def serve_admin_spa(full_path: str):
    return _index_response()
