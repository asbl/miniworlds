from __future__ import annotations

import os
import asyncio
import logging
import hmac
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, load_settings
from .db import Base, make_engine, make_session_factory
from .models import Project, ProjectRemote, User
from .migrations import migrate
from .maintenance import run_maintenance
from .locking import async_write_lock, storage_lock
from .services import cleanup_orphan_snapshots
from .request_limits import buffer_request
from .routes import admin_api, auth_api, gallery_api, pages, play_api, player_api, share_api, teacher_api
from .security import RateLimiter, decrypt_code, decrypt_secret, encryption_key_check, hash_password
from .yearly import get_setting, set_setting

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


def init_settings(db, settings: Settings) -> None:
    check = encryption_key_check(settings.secret_key)
    previous = get_setting(db, "encryption_key_check")
    if previous and not hmac.compare_digest(previous, check):
        raise ValueError("SECRET_KEY passt nicht zur vorhandenen Datenbank. Den bisherigen Schlüssel verwenden.")
    if previous is None:
        from cryptography.fernet import InvalidToken
        try:
            project = db.query(Project).first()
            remote = db.query(ProjectRemote).filter(ProjectRemote.token_enc.is_not(None)).first()
            if project:
                decrypt_code(project.code_enc, settings.secret_key)
            if remote:
                decrypt_secret(remote.token_enc, settings.secret_key)
        except InvalidToken:
            raise ValueError("SECRET_KEY kann die vorhandenen Zugangsdaten nicht entschlüsseln. Den bisherigen Schlüssel verwenden.") from None
        set_setting(db, "encryption_key_check", check)
    defaults = {
        "teacher_quota_cap": str(settings.teacher_quota_cap),
        "student_default_quota": str(settings.default_quota_bytes),
        "last_yearly_reset": "0",
        "declaration_version": "1",
    }
    for k, v in defaults.items():
        if get_setting(db, k) is None:
            set_setting(db, k, v)
    db.commit()


def seed_admin(db, settings: Settings) -> None:
    if not settings.admin_email or not settings.admin_password:
        return
    existing = db.query(User).filter_by(role="admin").first()
    if existing:
        return
    db.add(User(role="admin", email=settings.admin_email.lower(), pw_hash=hash_password(settings.admin_password)))
    db.commit()


def create_app(settings: Settings | None = None, enable_yearly_task: bool = True) -> FastAPI:
    settings = settings or load_settings()
    settings.validate()

    if settings.database_url.startswith("sqlite:///"):
        path = settings.database_url.removeprefix("sqlite:///")
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    os.makedirs(settings.media_root, exist_ok=True)
    os.makedirs(settings.git_root, exist_ok=True)

    engine = make_engine(settings.database_url)
    SessionLocal = make_session_factory(engine)
    try:
        with storage_lock(settings, exclusive=True):
            Base.metadata.create_all(engine)
            migrate(engine)
            with SessionLocal() as db:
                init_settings(db, settings)
                seed_admin(db, settings)
                cleanup_orphan_snapshots(db, settings)
    except Exception:
        engine.dispose()
        raise

    async def maintenance_loop():
        while True:
            try:
                job = asyncio.create_task(asyncio.to_thread(run_maintenance, SessionLocal, settings))
                try:
                    await asyncio.shield(job)
                except asyncio.CancelledError:
                    await job
                    raise
            except Exception:
                logging.getLogger(__name__).exception("Backend-Wartung fehlgeschlagen")
            await asyncio.sleep(1800)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(maintenance_loop()) if enable_yearly_task else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    app = FastAPI(title="miniworlds backend", lifespan=lifespan)
    app.state.settings = settings
    app.state.SessionLocal = SessionLocal
    app.state.engine = engine
    app.state.enable_yearly_task = enable_yearly_task
    app.state.rate_limiter = RateLimiter()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(pages.router)
    app.include_router(auth_api.router)
    app.include_router(admin_api.router)
    app.include_router(teacher_api.router)
    app.include_router(play_api.router)
    app.include_router(share_api.router)
    app.include_router(share_api.teacher_router)
    app.include_router(share_api.admin_router)
    app.include_router(gallery_api.router)
    app.include_router(gallery_api.admin_router)
    app.include_router(player_api.router)
    # Nur Schülerzugriffe benötigen CORS; Cookie-Sitzungen werden nicht freigegeben.
    app.add_middleware(CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()],
        allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"], expose_headers=["Content-Disposition"])

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        state = request.app.state
        response = None
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Klassen-/Lehreraktionen können viele Projekte betreffen. Sie
            # dürfen nicht mit Schüler-Schreibzugriffen oder Sicherungen laufen.
            if request.url.path.startswith("/api/"):
                response = await buffer_request(request, state.settings)
            if response is None:
                exclusive = request.url.path.startswith(("/api/teacher/", "/api/admin/")) or request.url.path in {"/api/claim", "/api/play/password"}
                async with async_write_lock(state.settings, exclusive=exclusive):
                    response = await call_next(request)
        else:
            response = await call_next(request)
        pyodide_base = state.settings.pyodide_base.rstrip("/") + "/"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'self'; "
            f"script-src 'self' 'wasm-unsafe-eval' {pyodide_base}; "
            f"connect-src 'self' {pyodide_base}; "
            "img-src 'self' data: blob:; media-src 'self' blob:; worker-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline'; frame-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if request.url.path == "/runner":
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                f"script-src 'self' 'unsafe-eval' 'wasm-unsafe-eval' {pyodide_base}; "
                f"connect-src {pyodide_base}; worker-src blob:; "
                "img-src data: blob:; media-src blob:; style-src 'unsafe-inline'; "
                "sandbox allow-scripts; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
            )
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith(("/api/", "/teacher", "/play", "/admin")) else "no-cache"
        if state.settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    return app
