from __future__ import annotations

import json
import base64
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import log_audit
from ..config import Settings
from ..deps import get_db, get_settings, get_student_project, require_admin, require_csrf, require_teacher
from ..models import MediaAsset, Project, Save, ShareRequest, Snapshot, User, utcnow
from ..security import decrypt_code
from ..services import compute_used_bytes, project_media_dir, snapshot_media_dir
from ..yearly import get_setting

router = APIRouter(tags=["share"])

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,59}$")

DECLARATION_TEXT = (
    "Ich versichere, dass das Programm und alle enthaltenen Bilder, Videos und Sounds "
    "keine Urheberrechte Dritter verletzen. Bei Minderjährigen bestätige ich, dass die "
    "Erziehungsberechtigten zugestimmt haben."
)


def _declaration_version(db: Session, settings: Settings) -> str:
    return get_setting(db, "declaration_version", "1") or "1"


def _serialize_request(db: Session, sr: ShareRequest, settings: Settings) -> dict:
    p = db.get(Project, sr.project_id)
    media = [
        {
            "id": a.id,
            "orig_name": a.orig_name,
            "mime": a.mime,
            "size_bytes": a.size_bytes,
            "license": a.license,
            "license_text": a.license_text,
            "source": a.source,
        }
        for a in db.query(MediaAsset).filter_by(project_id=sr.project_id).order_by(MediaAsset.id).all()
    ]
    save = db.get(Save, sr.project_id)
    return {
        "id": sr.id,
        "project_id": sr.project_id,
        "code": decrypt_code(p.code_enc, settings.secret_key) if p else None,
        "status": sr.status,
        "slug": sr.slug,
        "declaration_version": sr.declaration_version,
        "declared_at": sr.declared_at.isoformat() if sr.declared_at else None,
        "decided_at": sr.decided_at.isoformat() if sr.decided_at else None,
        "save_size_bytes": save.size_bytes if save else 0,
        "used_bytes": compute_used_bytes(db, p) if p else 0,
        "media": media,
    }


# ---------- Schüler ----------


class ShareRequestIn(BaseModel):
    declaration_accepted: bool


@router.post("/api/play/share-request")
def create_share_request(
    body: ShareRequestIn,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not body.declaration_accepted:
        raise HTTPException(400, "Die Versicherung muss bestätigt werden")
    existing = db.query(ShareRequest).filter_by(project_id=p.id, status="pending").first()
    if existing:
        raise HTTPException(409, "Es liegt bereits ein offener Antrag vor")
    sr = ShareRequest(project_id=p.id, status="pending", declaration_version=_declaration_version(db, settings))
    db.add(sr)
    log_audit(db, "code", f"project:{p.id}", "share_requested", target=f"share:{sr.id}", meta={"declaration_version": sr.declaration_version})
    db.commit()
    return {"ok": True, "id": sr.id, "status": "pending", "declaration_text": DECLARATION_TEXT}


@router.get("/api/play/share-status")
def share_status(p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    sr = db.query(ShareRequest).filter_by(project_id=p.id).order_by(ShareRequest.id.desc()).first()
    if not sr:
        return {"status": None, "slug": None, "declaration_text": DECLARATION_TEXT, "declaration_version": _declaration_version(db, settings)}
    snap = None
    if sr.slug:
        snap = db.query(Snapshot).filter_by(slug=sr.slug, active=True).order_by(Snapshot.version.desc()).first()
    return {
        "status": sr.status,
        "slug": sr.slug,
        "snapshot_version": snap.version if snap else None,
        "declaration_text": DECLARATION_TEXT,
        "declaration_version": sr.declaration_version,
    }


# ---------- Lehrer ----------

teacher_router = APIRouter(prefix="/api/teacher", tags=["teacher-share"], dependencies=[Depends(require_teacher), Depends(require_csrf)])


@teacher_router.get("/share-requests")
def teacher_share_requests(teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    project_ids = [p.id for p in db.query(Project).filter_by(teacher_id=teacher.id).all()]
    rows = db.query(ShareRequest).filter(ShareRequest.project_id.in_(project_ids)).order_by(ShareRequest.id.desc()).all() if project_ids else []
    return {"requests": [_serialize_request(db, r, settings) for r in rows]}


def _owned_share_request(db: Session, teacher: User, rid: int) -> ShareRequest:
    sr = db.get(ShareRequest, rid)
    if not sr:
        raise HTTPException(404, "Antrag nicht gefunden")
    p = db.get(Project, sr.project_id)
    if not p or p.teacher_id != teacher.id:
        raise HTTPException(404, "Antrag nicht gefunden")
    return sr


def _make_slug(db: Session, custom: str | None, project_id: int) -> str:
    if custom:
        slug = custom.strip().lower()
        if not SLUG_RE.match(slug):
            raise HTTPException(400, "Slug: nur a-z, 0-9, '-', 3-60 Zeichen, muss mit Buchstabe/Zahl beginnen")
        if db.query(Snapshot).filter_by(slug=slug).first():
            raise HTTPException(409, "Slug bereits vergeben")
        return slug
    while True:
        slug = f"projekt-{project_id}-{secrets.token_hex(3)}"
        if not db.query(Snapshot).filter_by(slug=slug).first():
            return slug


@teacher_router.post("/share-requests/{rid}/approve")
def approve_share(
    rid: int,
    body: dict,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Freigabe: friert den aktuellen Stand als Snapshot ein (Save + Medien + Lizenzen, Dateien kopiert)."""
    sr = _owned_share_request(db, teacher, rid)
    if sr.status != "pending":
        raise HTTPException(409, f"Antrag ist nicht offen (Status: {sr.status})")
    slug = _make_slug(db, body.get("slug"), sr.project_id)

    p = db.get(Project, sr.project_id)
    save = db.get(Save, p.id)
    media_rows = db.query(MediaAsset).filter_by(project_id=p.id).order_by(MediaAsset.id).all()
    from ..archives import media_name
    files = json.loads(save.payload).get("files") if save else None
    frozen_media = {}
    for asset in media_rows:
        name = media_name(asset.id, asset.orig_name)
        if files is not None:
            if name not in files:
                continue
            frozen_media[asset.id] = base64.b64decode(files[name])
        else:
            path = project_media_dir(settings, p.id) / asset.stored_name
            if not path.is_file():
                raise HTTPException(409, "Eine Mediendatei fehlt. Bitte erneut hochladen.")
            frozen_media[asset.id] = path.read_bytes()
    media_rows = [a for a in media_rows if a.id in frozen_media]
    payload = {
        "project_id": p.id,
        "frozen_at": utcnow().isoformat(),
        "save": json.loads(save.payload) if save else None,
        "media": [
            {
                "asset_id": a.id,
                "stored_name": a.stored_name,
                "orig_name": a.orig_name,
                "mime": a.mime,
                "size_bytes": len(frozen_media[a.id]),
                "license": a.license,
                "license_text": a.license_text,
                "source": a.source,
            }
            for a in media_rows
        ],
    }
    # alte aktive Snapshots dieses Projekts deaktivieren? Nein: slug ist unique — mehrere Freigaben über Zeit erzeugen neue Slugs/Versionen.
    snap = Snapshot(
        share_request_id=sr.id,
        project_id=p.id,
        slug=slug,
        version=1,
        active=True,
        payload=json.dumps(payload, ensure_ascii=False).encode(),
    )
    db.add(snap)
    db.flush()
    # Mediendateien in den Snapshot-Ordner kopieren (unabhängig vom Projekt)
    dst_dir = snapshot_media_dir(settings, snap.id)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for a in media_rows:
        (dst_dir / a.stored_name).write_bytes(frozen_media[a.id])
    sr.status = "approved"
    sr.slug = slug
    sr.decided_at = utcnow()
    sr.decided_by = teacher.id
    log_audit(db, "teacher", f"user:{teacher.id}", "share_approved", target=f"share:{rid}", meta={"slug": slug, "snapshot": snap.id, "project": p.id})
    db.commit()
    return {"ok": True, "status": "approved", "slug": slug, "url": f"/p/{slug}", "snapshot_id": snap.id}


@teacher_router.post("/share-requests/{rid}/reject")
def reject_share(rid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    sr = _owned_share_request(db, teacher, rid)
    if sr.status != "pending":
        raise HTTPException(409, "Antrag ist nicht offen")
    sr.status = "rejected"
    sr.decided_at = utcnow()
    sr.decided_by = teacher.id
    log_audit(db, "teacher", f"user:{teacher.id}", "share_rejected", target=f"share:{rid}", meta={"project": sr.project_id})
    db.commit()
    return {"ok": True, "status": "rejected"}


@teacher_router.post("/share-requests/{rid}/revoke")
def revoke_share(rid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    sr = _owned_share_request(db, teacher, rid)
    if sr.status != "approved":
        raise HTTPException(409, "Nur freigegebene Anträge können widerrufen werden")
    if sr.slug:
        snap = db.query(Snapshot).filter_by(slug=sr.slug, active=True).first()
        if snap:
            snap.active = False
    sr.status = "revoked"
    sr.decided_at = utcnow()
    sr.decided_by = teacher.id
    log_audit(db, "teacher", f"user:{teacher.id}", "share_revoked", target=f"share:{rid}", meta={"slug": sr.slug, "project": sr.project_id})
    db.commit()
    return {"ok": True, "status": "revoked"}


# ---------- Admin ----------

admin_router = APIRouter(prefix="/api/admin", tags=["admin-share"], dependencies=[Depends(require_admin), Depends(require_csrf)])


@admin_router.get("/share-requests")
def admin_share_requests(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = db.query(ShareRequest).order_by(ShareRequest.id.desc()).all()
    return {"requests": [_serialize_request(db, r, settings) for r in rows]}


# ---------- Öffentlich: /p/<slug> ----------


def _active_snapshot(db: Session, slug: str) -> Snapshot | None:
    return db.query(Snapshot).filter_by(slug=slug, active=True).order_by(Snapshot.version.desc()).first()


@router.get("/p/{slug}", response_class=HTMLResponse, include_in_schema=False)
def public_page(slug: str, request: Request, db: Session = Depends(get_db)):
    snap = _active_snapshot(db, slug)
    if not snap:
        raise HTTPException(404, "Projekt nicht (mehr) öffentlich verfügbar")
    payload = json.loads(snap.payload)
    return TEMPLATES.TemplateResponse(
        request,
        "public.html",
        {
            "page": "public",
            "slug": snap.slug,
            "version": snap.version,
            "frozen_at": payload.get("frozen_at"),
            "save": payload.get("save"),
            "media": payload.get("media", []),
        },
    )


@router.get("/api/public/{slug}")
def public_payload(slug: str, db: Session = Depends(get_db)):
    snap = _active_snapshot(db, slug)
    if not snap:
        raise HTTPException(404, "nicht verfügbar")
    return json.loads(snap.payload) | {"slug": snap.slug, "version": snap.version}


@router.get("/api/public/{slug}/media/{asset_id}")
def public_media(slug: str, asset_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    snap = _active_snapshot(db, slug)
    if not snap:
        raise HTTPException(404, "nicht verfügbar")
    payload = json.loads(snap.payload)
    item = next((m for m in payload.get("media", []) if m["asset_id"] == asset_id), None)
    if not item:
        raise HTTPException(404, "Medium nicht in diesem Snapshot")
    path = snapshot_media_dir(settings, snap.id) / item["stored_name"]
    if not path.exists():
        raise HTTPException(404, "Datei fehlt")
    return FileResponse(path, media_type=item["mime"], headers={"X-Content-Type-Options": "nosniff"})


class ReportIn(BaseModel):
    reason: str


@router.post("/api/public/{slug}/report")
def public_report(slug: str, body: ReportIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    if not request.app.state.rate_limiter.allow(f"report:{ip}", 5, 300):
        raise HTTPException(429, "Zu viele Meldungen")
    snap = _active_snapshot(db, slug)
    if not snap:
        raise HTTPException(404, "nicht verfügbar")
    log_audit(
        db,
        "anonymous",
        ip,
        "public_report",
        target=f"snapshot:{snap.id}",
        meta={"slug": slug, "reason": body.reason[:1000]},
    )
    db.commit()
    return {"ok": True, "message": "Danke — der Lehrer/Admin wurde informiert (Audit-Log)."}
