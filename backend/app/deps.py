from __future__ import annotations

import hmac
from contextlib import nullcontext

from fastapi import Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from .config import Settings
from .models import Project, Session as DbSession, User, aware, utcnow
from .security import csrf_token, hash_token, verify_student_token
from .locking import project_write_lock


def get_db(request: Request):
    db: Session = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("session")
    if not token:
        return None
    sess = db.query(DbSession).filter_by(token_hash=hash_token(token)).first()
    if not sess or aware(sess.expires_at) < utcnow():
        return None
    user = db.get(User, sess.user_id)
    if not user or user.disabled:
        return None
    return user


def require_role(role: str):
    def dep(request: Request, db: Session = Depends(get_db)) -> User:
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(401, "Nicht angemeldet")
        if user.role != role:
            raise HTTPException(403, "Keine Berechtigung für diese Rolle")
        return user

    return dep


require_admin = require_role("admin")
require_teacher = require_role("teacher")


def require_csrf(request: Request) -> None:
    """Double-Submit-Check für Cookie-authentifizierte unsafe Requests (JSON-API)."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, "Nicht angemeldet")
    header = request.headers.get("X-CSRF-Token", "")
    expected = csrf_token(request.app.state.settings.secret_key, token)
    if not hmac.compare_digest(header, expected):
        raise HTTPException(403, "CSRF-Token fehlt oder ist ungültig")


async def get_student_project(request: Request, db: Session = Depends(get_db)):
    """Schüler-Authentifizierung per signiertem Bearer-Token (an Code-Hash gebunden)."""
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    payload = verify_student_token(request.app.state.settings.secret_key, token)
    if not payload:
        raise HTTPException(401, "Ungültiger oder abgelaufener Token")
    settings = request.app.state.settings
    lock = project_write_lock(settings, int(payload["pid"])) if request.method in {"POST", "PUT", "PATCH", "DELETE"} else nullcontext()
    async with lock:
        project = await run_in_threadpool(db.get, Project, int(payload["pid"]))
        if not project or not hmac.compare_digest(project.code_hash[:16], str(payload["ch"])):
            raise HTTPException(401, "Token passt nicht mehr zum Code (Code wurde geändert?)")
        yield project
