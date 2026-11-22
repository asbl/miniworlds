from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .. import gitstore
from ..config import Settings
from ..deps import get_settings

router = APIRouter(tags=["player"])


@router.get("/wheel/miniworlds.whl", include_in_schema=False)
def wheel(settings: Settings = Depends(get_settings)):
    raw = settings.miniworlds_wheel_path
    path = Path(raw) if raw else None
    if not path or not path.is_file():
        raise HTTPException(404, "miniworlds-Wheel nicht gebaut — siehe backend/README (pip wheel source ...)")
    return FileResponse(path, media_type="application/octet-stream", filename="miniworlds.whl")


@router.get("/api/player/config")
def player_config(settings: Settings = Depends(get_settings)):
    return {
        "pyodide_base": settings.pyodide_base.rstrip("/") + "/",
        "wheel_url": "/wheel/miniworlds.whl",
        "wheel_available": bool(settings.miniworlds_wheel_path and Path(settings.miniworlds_wheel_path).is_file()),
        "git_available": gitstore.git_available(),
    }
