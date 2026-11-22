from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import PublicTask

router = APIRouter(tags=["pages"])

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/play")


@router.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}


@router.get("/admin/login", response_class=HTMLResponse, include_in_schema=False)
def admin_login(request: Request):
    return TEMPLATES.TemplateResponse(request, "login.html", {"role": "admin", "page": "login"})


@router.get("/teacher/login", response_class=HTMLResponse, include_in_schema=False)
def teacher_login(request: Request):
    return TEMPLATES.TemplateResponse(request, "login.html", {"role": "teacher", "page": "login"})


@router.get("/teacher/claim", response_class=HTMLResponse, include_in_schema=False)
def teacher_claim(request: Request):
    return TEMPLATES.TemplateResponse(request, "claim.html", {"page": "claim"})


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/admin/login", status_code=302)
    return TEMPLATES.TemplateResponse(request, "admin.html", {"user": user, "page": "admin"})


@router.get("/teacher", response_class=HTMLResponse, include_in_schema=False)
def teacher_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "teacher":
        return RedirectResponse("/teacher/login", status_code=302)
    return TEMPLATES.TemplateResponse(request, "teacher.html", {"user": user, "page": "teacher"})


@router.get("/play", response_class=HTMLResponse, include_in_schema=False)
def play_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "play.html", {"page": "play"})


@router.get("/runner", response_class=HTMLResponse, include_in_schema=False)
def runner_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "runner.html", {})


@router.get("/player", response_class=HTMLResponse, include_in_schema=False)
def player_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "player.html", {"page": "player"})


@router.get("/t/{slug}", response_class=HTMLResponse, include_in_schema=False)
def public_task_page(slug: str, request: Request, db: Session = Depends(get_db)):
    pt = db.query(PublicTask).filter_by(slug=slug, status="published").first()
    if not pt:
        raise HTTPException(404, "Aufgabe nicht öffentlich verfügbar")
    return TEMPLATES.TemplateResponse(
        request,
        "public_task.html",
        {
            "page": "public_task",
            "slug": pt.slug,
            "title": pt.title,
            "description": pt.description,
            "items": json.loads(pt.items),
            "author_alias": pt.author_alias,
            "school": pt.school,
            "license": pt.license,
            "version": pt.version,
            "published_at": pt.published_at.isoformat() if pt.published_at else None,
        },
    )
