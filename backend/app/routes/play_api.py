from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session

from .. import gitstore
from ..archives import media_name, pack_snapshot, project_snapshot, project_zip, unpack_snapshot
from ..projects import new_project, read_only_reason, require_writable, store_save, require_active_code, student_binding, copy_project_content, code_expiry
from ..audit import log_audit
from ..config import Settings
from ..deps import get_db, get_settings, get_student_project
from ..models import MediaAsset, Project, ProjectRemote, Save, ShareRequest, Submission, SubmissionVersion, Task, TaskAssignment, TemplateCode, Workspace, CodeAttempt, aware, utcnow
from ..security import decrypt_secret, encrypt_secret, hash_code, make_student_token, hash_password, verify_password
from ..storage import limit_submissions, storage_policy
from ..editor_files import save_payload
from ..services import (
    ALLOWED_MEDIA,
    LICENSE_CHOICES,
    MAX_MEDIA_FILE_BYTES,
    check_media_head,
    compute_used_bytes,
    decode_answers,
    project_media_dir,
)

router = APIRouter(prefix="/api", tags=["play"])


class ClaimIn(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    password: str = Field(default="", max_length=256)


@router.post("/claim")
def claim_code(body: ClaimIn, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Schüler-Code einlösen → signiertes Bearer-Token (an Code-Hash gebunden)."""
    ip = request.client.host if request.client else "?"
    if not request.app.state.rate_limiter.allow(f"claim-request:{ip}", 600, 60):
        raise HTTPException(429, "Zu viele Versuche")
    ch = hash_code(body.code)
    attempt = db.get(CodeAttempt, ch)
    if attempt and aware(attempt.expires_at) > utcnow() and attempt.failures >= 5:
        raise HTTPException(429, "Zu viele Fehlversuche für diesen Zugang. Bitte fünf Minuten warten.")
    if request.app.state.rate_limiter.limited(f"claim-failed:{ip}", 20, 60):
        raise HTTPException(429, "Zu viele ungültige Codes. Bitte eine Minute warten.")
    p = db.query(Project).filter_by(code_hash=ch).first()
    personal_code = None
    invite = db.query(TemplateCode).filter_by(code_hash=ch).first() if not p else None
    if invite and not invite.used_at and (not invite.expires_at or aware(invite.expires_at) > utcnow()):
        source = db.get(Project, invite.project_id)
        snapshot = project_snapshot(db, settings, source)
        p, personal_code = new_project(db, settings, source.teacher_id, source.course_id, title=source.title)
        try:
            copy_project_content(db, settings, p, snapshot)
            for task in db.query(Task).join(TaskAssignment).filter(TaskAssignment.project_id == source.id):
                if not db.query(TaskAssignment).filter_by(project_id=p.id, task_id=task.id).first():
                    assignment = TaskAssignment(project_id=p.id, task_id=task.id)
                    db.add(assignment)
                    db.flush()
                    db.add(Submission(assignment_id=assignment.id, project_id=p.id))
            if compute_used_bytes(db, p) > p.quota_bytes:
                raise HTTPException(413, "Die Vorlage ist zu groß. Bitte die Lehrkraft fragen.")
            invite.used_at = utcnow()
            db.commit()
        except Exception:
            pid = p.id
            db.rollback()
            from ..services import delete_project_files
            delete_project_files(settings, pid)
            raise
    workspace = db.get(Workspace, p.workspace_id) if p and p.workspace_id else None
    valid = p is not None and (not workspace or not workspace.password_hash or verify_password(body.password, workspace.password_hash))
    if not valid:
        from datetime import timedelta
        request.app.state.rate_limiter.allow(f"claim-failed:{ip}", 20, 60)
        if not attempt or aware(attempt.expires_at) <= utcnow():
            if attempt:
                db.delete(attempt)
                db.flush()
            attempt = CodeAttempt(key=ch, failures=0, expires_at=utcnow()+timedelta(minutes=5))
            db.add(attempt)
        attempt.failures += 1
        db.query(CodeAttempt).filter(CodeAttempt.expires_at < utcnow()).delete(synchronize_session=False)
        db.commit()
        raise HTTPException(401, "Code oder Passwort ungültig, oder Zugang abgelaufen.")
    require_active_code(db, p)
    if attempt:
        db.delete(attempt)
        db.commit()
    token = make_student_token(settings.secret_key, p.id, student_binding(db, p), settings.student_token_hours)
    return {"token": token, "project_id": p.id, "read_only": bool(read_only_reason(db, p)), "personal_code": personal_code}


@router.get("/play/project")
def get_project(p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    save = db.get(Save, p.id)
    tasks = []
    for a in db.query(TaskAssignment).filter_by(project_id=p.id).order_by(TaskAssignment.id).all():
        t = db.get(Task, a.task_id)
        if not t:
            continue
        sub = db.query(Submission).filter_by(assignment_id=a.id).first()
        definition = {"title": t.title, "description": t.description,
                      "items": [{"id": i.id, "kind": i.kind, "prompt": i.prompt, "position": i.position}
                                for i in sorted(t.items, key=lambda i: i.position)]}
        if sub and sub.status == "submitted":
            version = db.query(SubmissionVersion).filter_by(submission_id=sub.id, version=sub.current_version).first()
            if version and version.project_snapshot:
                definition = unpack_snapshot(version.project_snapshot)["task"]
        tasks.append(
            {
                "assignment_id": a.id,
                "task_id": t.id,
                "title": definition["title"],
                "description": definition["description"],
                "status": sub.status if sub else "open",
                "version": sub.current_version if sub else 0,
                "submitted_at": sub.submitted_at.isoformat() if sub and sub.submitted_at else None,
                "items": definition["items"],
                "answers": decode_answers(db, sub),
            }
        )
    sr = db.query(ShareRequest).filter_by(project_id=p.id).order_by(ShareRequest.id.desc()).first()
    media = db.query(MediaAsset).filter_by(project_id=p.id).order_by(MediaAsset.id).all()
    return {
        "project_id": p.id,
        "title": p.title,
        "revision": p.revision,
        "workspace_id": p.workspace_id,
        "course_id": p.course_id,
        "read_only": bool(read_only_reason(db, p)),
        "read_only_reason": read_only_reason(db, p),
        "quota_bytes": p.quota_bytes,
        "used_bytes": compute_used_bytes(db, p),
        "storage_policy": storage_policy(settings),
        "save": json.loads(save.payload) if save else None,
        "tasks": tasks,
        "media": [_serialize_media(a) for a in media],
        "license_choices": LICENSE_CHOICES,
        "share": {"status": sr.status, "slug": sr.slug} if sr else None,
        "code_expires_at": code_expiry(db, p),
        "password_protected": bool(db.get(Workspace, p.workspace_id).password_hash) if p.workspace_id else False,
    }


class StudentProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)


@router.get("/play/projects")
def workspace_projects(p: Project = Depends(get_student_project), db: Session = Depends(get_db)):
    rows = db.query(Project).filter_by(workspace_id=p.workspace_id, teacher_id=p.teacher_id).order_by(Project.id).all() if p.workspace_id else [p]
    return {"projects": [{"id": r.id, "title": r.title, "read_only": bool(read_only_reason(db, r))} for r in rows]}


@router.post("/play/projects")
def create_student_project(body: StudentProjectIn, p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    require_writable(db, p)
    if not body.title.strip():
        raise HTTPException(422, "Bitte einen Projekttitel eingeben")
    if db.query(Project).filter_by(workspace_id=p.workspace_id).count() >= 30:
        raise HTTPException(409, "In diesem Arbeitsbereich sind bereits 30 Projekte vorhanden")
    project, _ = new_project(db, settings, p.teacher_id, p.course_id, p.workspace_id, body.title.strip())
    db.commit()
    return {"project_id": project.id, "token": make_student_token(settings.secret_key, project.id, student_binding(db, project), settings.student_token_hours)}


@router.post("/play/projects/{pid}/open")
def open_student_project(pid: int, p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    project = db.get(Project, pid)
    if not project or not p.workspace_id or project.workspace_id != p.workspace_id or project.teacher_id != p.teacher_id:
        raise HTTPException(404, "Projekt nicht gefunden")
    require_active_code(db, project)
    return {"project_id": project.id, "token": make_student_token(settings.secret_key, project.id, student_binding(db, project), settings.student_token_hours)}


class PasswordIn(BaseModel):
    current_password: str = Field(default="", max_length=256)
    password: str = Field(min_length=12, max_length=256)


@router.put("/play/password")
def protect_project(body: PasswordIn, request: Request, p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    workspace = db.get(Workspace, p.workspace_id)
    if not request.app.state.rate_limiter.allow(f"password:{workspace.id}", 5, 300):
        raise HTTPException(429, "Bitte fünf Minuten warten.")
    if workspace.password_hash and not verify_password(body.current_password, workspace.password_hash):
        raise HTTPException(401, "Aktuelles Passwort ungültig")
    workspace.password_hash = hash_password(body.password)
    workspace.credential_version += 1
    db.commit()
    return {"ok": True, "token": make_student_token(settings.secret_key, p.id, student_binding(db, p), settings.student_token_hours)}


class SaveIn(BaseModel):
    base_revision: int = Field(default=0, ge=0)
    source: str
    db: str | None = None
    message: str | None = None  # optionaler Commit-Kommentar für den Versionsverlauf
    files: dict[str, str] | None = None  # relative Pfade → Base64, für den eigenständigen Editor


def _decode_db(db: str | None) -> bytes | None:
    """db-Feld aus dem Save-Payload als Bytes; bei ungültigem base64 Roh-Bytes (nie fehlschlagen)."""
    if not db:
        return None
    try:
        return base64.b64decode(db + "=" * (-len(db) % 4))
    except (ValueError, binascii.Error):
        return db.encode("utf-8")


def _commit_save_to_git(db: Session, settings: Settings, p: Project, body: SaveIn) -> tuple[str | None, str | None]:
    """Speichert einen git-Commit zum Save. Fehler landen nur im Audit-Log, nie im Save."""
    if not gitstore.git_available():
        return None, None
    try:
        db_bytes = _decode_db(body.db)
        message = (body.message or "").strip() or f"Speichern am {utcnow():%d.%m.%Y, %H:%M} Uhr"
        return gitstore.commit_save(settings, p.id, body.source, db_bytes, message, body.files), None
    except gitstore.GitError as error:
        log_audit(db, "code", f"project:{p.id}", "git_commit_failed", meta={"error": str(error)})
        db.commit()
        return None, str(error)


@router.put("/play/save")
def put_save(
    body: SaveIn,
    request: Request,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"save:{p.id}", 60, 60):
        raise HTTPException(429, "Zu viele Speicher-Vorgänge")
    old = db.get(Save, p.id)
    # Alte Player dürfen ergänzende Dateien nicht versehentlich entfernen.
    files = body.files if body.files is not None else (json.loads(old.payload).get("files") if old else None)
    data = save_payload(body.source, body.db, files)
    body.files = data.get("files")
    removed_media = []
    if body.files is not None:
        for asset in db.query(MediaAsset).filter_by(project_id=p.id).all():
            if media_name(asset.id, asset.orig_name) not in body.files:
                removed_media.append(project_media_dir(settings, p.id) / asset.stored_name)
                db.delete(asset)
    payload = json.dumps(data).encode()
    revision = store_save(db, p, payload, body.base_revision)
    db.commit()
    for path in removed_media:
        path.unlink(missing_ok=True)
    commit_hash, warning = _commit_save_to_git(db, settings, p, body)
    return {"ok": True, "used_bytes": compute_used_bytes(db, p), "quota_bytes": p.quota_bytes, "commit": commit_hash, "revision": revision, "warning": warning}


# ---------- Versionsverlauf (git) ----------


@router.get("/play/history")
def play_history(
    p: Project = Depends(get_student_project),
    settings: Settings = Depends(get_settings),
    limit: int = 50,
):
    """Commits des Projekts, neueste zuerst. available=False wenn git fehlt oder es noch keinen Verlauf gibt."""
    if not gitstore.git_available():
        return {"available": False, "commits": []}
    return {"available": True, "commits": gitstore.history(settings, p.id, max(1, min(limit, 200))),
            "used_bytes": gitstore.history_bytes(settings, p.id), "max_bytes": settings.history_max_bytes,
            "paused": gitstore.history_paused(settings, p.id)}


@router.delete("/play/history")
def clear_history(base_revision: int = Query(ge=0), p: Project = Depends(get_student_project),
                  db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    require_writable(db, p)
    if gitstore.remote_url(settings, p.id):
        raise HTTPException(409, "Vor dem Löschen des Verlaufs muss das Git-Remote entfernt werden. Der externe Verlauf bleibt dort erhalten.")
    locked = db.execute(update(Project).where(Project.id == p.id, Project.revision == base_revision)
                        .values(revision=Project.revision + 1).execution_options(synchronize_session=False))
    if locked.rowcount != 1:
        raise HTTPException(409, "Der Projektstand hat sich geändert. Bitte neu laden.")
    gitstore.delete_repo(settings, p.id)
    log_audit(db, "code", f"project:{p.id}", "git_history_deleted")
    db.commit()
    db.refresh(p)
    return {"ok": True, "revision": p.revision}


@router.get("/play/history/download")
def download_history(p: Project = Depends(get_student_project), settings: Settings = Depends(get_settings)):
    try:
        content = gitstore.history_bundle(settings, p.id)
    except gitstore.GitError as error:
        raise HTTPException(409, str(error)) from None
    return Response(content=content, media_type="application/octet-stream",
                    headers={"Content-Disposition": 'attachment; filename="miniworlds-verlauf.bundle"'})


@router.get("/play/history/{commit}")
def play_history_detail(commit: str, p: Project = Depends(get_student_project), settings: Settings = Depends(get_settings)):
    """Metadaten + Diff eines Commits."""
    if not gitstore.git_available():
        raise HTTPException(503, "git ist auf dem Server nicht verfügbar")
    try:
        return {"hash": commit, "show": gitstore.show(settings, p.id, commit)}
    except gitstore.GitError as error:
        raise HTTPException(404, str(error)) from None


@router.post("/play/restore/{commit}")
def play_restore(
    commit: str,
    request: Request,
    base_revision: int | None = Query(default=None, ge=0),
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Alte Version aus dem git-Verlauf als aktuellen Save übernehmen (erzeugt selbst wieder einen Commit)."""
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"restore:{p.id}", 60, 60):
        raise HTTPException(429, "Zu viele Wiederherstellungs-Vorgänge")
    if not gitstore.git_available():
        raise HTTPException(503, "git ist auf dem Server nicht verfügbar")
    try:
        payload = gitstore.read_save_at(settings, p.id, commit)
    except gitstore.GitError as error:
        raise HTTPException(404, str(error)) from None
    data = json.loads(payload)
    revision = store_save(db, p, payload, base_revision)
    db.commit()
    commit_hash = None
    try:
        db_bytes = _decode_db(data.get("db"))
        commit_hash = gitstore.commit_save(settings, p.id, data["source"], db_bytes, f"Wiederhergestellt: {commit[:8]}", data.get("files"))
    except gitstore.GitError as error:
        log_audit(db, "code", f"project:{p.id}", "git_commit_failed", meta={"error": str(error)})
    log_audit(db, "code", f"project:{p.id}", "git_restore", target=commit[:8], meta={"commit": commit_hash})
    db.commit()
    return {"ok": True, "commit": commit_hash, "save": data, "revision": revision}


# ---------- Remote (Push/Pull, z. B. GitHub) ----------


class RemoteIn(BaseModel):
    url: str
    token: str | None = None  # leer = ohne Auth; wird verschlüsselt gespeichert und nie zurückgegeben


def _remote_token(db: Session, settings: Settings, p: Project) -> str | None:
    row = db.get(ProjectRemote, p.id)
    if row and row.token_enc:
        return decrypt_secret(row.token_enc, settings.secret_key)
    return None


def _require_configured_remote(settings: Settings, p: Project) -> None:
    if not gitstore.remote_url(settings, p.id):
        raise HTTPException(409, "Es ist noch kein Remote konfiguriert — zuerst Remote setzen.")


@router.get("/play/remote")
def play_get_remote(p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    row = db.get(ProjectRemote, p.id)
    url = row.url if row else gitstore.remote_url(settings, p.id)
    return {"configured": bool(url), "url": url, "has_token": bool(row and row.token_enc)}


@router.put("/play/remote")
def play_put_remote(
    body: RemoteIn,
    request: Request,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"remote:{p.id}", 20, 60):
        raise HTTPException(429, "Zu viele Remote-Vorgänge")
    try:
        url = gitstore.validate_remote_url(body.url, settings.git_allowed_hosts)
    except gitstore.GitError as error:
        raise HTTPException(400, str(error)) from None
    gitstore.set_remote(settings, p.id, url)
    row = db.get(ProjectRemote, p.id)
    if row is None:
        row = ProjectRemote(project_id=p.id)
        db.add(row)
    row.url = url
    row.updated_at = utcnow()
    token = (body.token or "").strip()
    row.token_enc = encrypt_secret(token, settings.secret_key) if token else None
    log_audit(db, "code", f"project:{p.id}", "git_remote_set", target=f"project:{p.id}", meta={"has_token": bool(token)})
    db.commit()
    return {"ok": True, "url": url, "has_token": bool(token)}


@router.delete("/play/remote")
def play_delete_remote(
    request: Request,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"remote:{p.id}", 20, 60):
        raise HTTPException(429, "Zu viele Remote-Vorgänge")
    gitstore.remove_remote(settings, p.id)
    row = db.get(ProjectRemote, p.id)
    if row:
        db.delete(row)
    log_audit(db, "code", f"project:{p.id}", "git_remote_removed")
    db.commit()
    return {"ok": True}


@router.post("/play/push")
def play_push(
    request: Request,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not request.app.state.rate_limiter.allow(f"push:{p.id}", 20, 60):
        raise HTTPException(429, "Zu viele Push-Vorgänge")
    if not gitstore.git_available():
        raise HTTPException(503, "git ist auf dem Server nicht verfügbar")
    _require_configured_remote(settings, p)
    row = db.get(ProjectRemote, p.id)
    try:
        branch = gitstore.push(settings, p.id, _remote_token(db, settings, p))
    except gitstore.GitError as error:
        raise HTTPException(502, str(error)) from None
    log_audit(db, "code", f"project:{p.id}", "git_push", target=f"project:{p.id}", meta={"branch": branch})
    db.commit()
    return {"ok": True, "branch": branch, "url": row.url if row else gitstore.remote_url(settings, p.id)}


@router.post("/play/pull")
def play_pull(
    request: Request,
    base_revision: int | None = Query(default=None, ge=0),
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"pull:{p.id}", 20, 60):
        raise HTTPException(429, "Zu viele Pull-Vorgänge")
    if not gitstore.git_available():
        raise HTTPException(503, "git ist auf dem Server nicht verfügbar")
    _require_configured_remote(settings, p)
    if base_revision is None:
        raise HTTPException(428, "Bitte zuerst den aktuellen Projektstand laden")
    old_head = gitstore.head_short(settings, p.id)
    try:
        new_head = gitstore.pull(settings, p.id, _remote_token(db, settings, p))
    except gitstore.GitError as error:
        raise HTTPException(502, str(error)) from None
    # Save-Zeile aus dem neuen HEAD übernehmen, damit Player und git synchron bleiben
    data = None
    try:
        payload = gitstore.read_save_at(settings, p.id, "HEAD")
    except gitstore.GitError:
        payload = None
    if payload is not None:
        data = json.loads(payload)
        try:
            store_save(db, p, payload, base_revision)
        except HTTPException:
            if old_head:
                gitstore.reset_head(settings, p.id, old_head)
            raise
    log_audit(db, "code", f"project:{p.id}", "git_pull", meta={"commit": new_head})
    db.commit()
    return {"ok": True, "commit": new_head, "save": data, "revision": p.revision}


@router.get("/play/download")
def download(p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return Response(content=project_zip(project_snapshot(db, settings, p)), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="miniworlds-project-{p.id}.zip"'})


class AnswersIn(BaseModel):
    base_version: int = Field(default=0, ge=0)
    answers: dict  # {item_id: {"checked": bool}}


@router.put("/play/tasks/{assignment_id}/answers")
def put_answers(
    assignment_id: int,
    body: AnswersIn,
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    a = db.get(TaskAssignment, assignment_id)
    if not a or a.project_id != p.id:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    sub = db.query(Submission).filter_by(assignment_id=assignment_id).first()
    if sub and sub.status == "submitted":
        raise HTTPException(409, "Bereits abgegeben — der Lehrer muss die Abgabe zuerst wieder öffnen")
    task = db.get(Task, a.task_id)
    items = {str(i.id): i for i in task.items}
    for key, answer in body.answers.items():
        item = items.get(key)
        if not item or not isinstance(answer, dict) or item.kind != "checkbox":
            raise HTTPException(422, "Antwort gehört nicht zu dieser Aufgabe")
        if set(answer) != {"checked"} or type(answer["checked"]) is not bool:
            raise HTTPException(422, "Nur Checkbox-Antworten ohne Freitext sind erlaubt")
    payload = json.dumps(body.answers).encode()
    cur_size = 0
    if sub and sub.current_version:
        v = db.query(SubmissionVersion).filter_by(submission_id=sub.id, version=sub.current_version).first()
        if v:
            cur_size = len(v.payload)
    used = compute_used_bytes(db, p)
    if used - cur_size + len(payload) > p.quota_bytes:
        raise HTTPException(413, "Quota überschritten durch Abgabe-Antworten")
    if not sub:
        sub = Submission(assignment_id=assignment_id, project_id=p.id, status="open", current_version=0)
        db.add(sub)
        db.flush()
    result = db.execute(update(Submission).where(Submission.id == sub.id, Submission.current_version == body.base_version,
                                               Submission.status == "open")
                        .values(current_version=Submission.current_version + 1)
                        .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Die Antworten wurden in einem anderen Tab geändert. Dein Entwurf bleibt lokal erhalten.")
    db.refresh(sub)
    # Nur eingereichte Fassungen dauerhaft behalten; alte automatische Entwürfe entfernen.
    db.query(SubmissionVersion).filter_by(submission_id=sub.id, submitted=False).delete()
    db.add(SubmissionVersion(submission_id=sub.id, version=sub.current_version, payload=payload, submitted=False))
    db.flush()
    limit_submissions(db, settings, p.id)
    db.commit()
    return {"ok": True, "version": sub.current_version, "used_bytes": compute_used_bytes(db, p)}


@router.post("/play/tasks/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    base_revision: int | None = Query(default=None, ge=0),
    settings: Settings = Depends(get_settings),
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
):
    require_writable(db, p)
    # Serialize with saves while copying the exact revision into the immutable snapshot.
    expected_revision = p.revision if base_revision is None else base_revision
    locked = db.execute(update(Project).where(Project.id == p.id, Project.revision == expected_revision)
                        .values(revision=Project.revision).execution_options(synchronize_session=False))
    if locked.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Der Projektstand wurde inzwischen geändert. Bitte vor der Abgabe neu laden.")
    db.refresh(p)
    a = db.get(TaskAssignment, assignment_id)
    if not a or a.project_id != p.id:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    sub = db.query(Submission).filter_by(assignment_id=assignment_id).first()
    if not sub:
        sub = Submission(assignment_id=assignment_id, project_id=p.id, status="open", current_version=0)
        db.add(sub)
        db.flush()
    if sub.status == "submitted":
        raise HTTPException(409, "Bereits abgegeben")
    payload = json.dumps(decode_answers(db, sub)).encode()
    if base_revision is not None and base_revision != p.revision:
        raise HTTPException(409, "Der Projektstand wurde inzwischen geändert. Bitte vor der Abgabe neu laden.")
    snapshot = pack_snapshot(project_snapshot(db, settings, p, db.get(Task, a.task_id)))
    sub.done = False
    sub.current_version += 1
    db.add(SubmissionVersion(submission_id=sub.id, version=sub.current_version, payload=payload, submitted=True, project_snapshot=snapshot))
    db.flush()
    limit_submissions(db, settings, p.id)
    sub.status = "submitted"
    sub.submitted_at = utcnow()
    log_audit(db, "code", f"project:{p.id}", "task_submitted", target=f"assignment:{assignment_id}", meta={"version": sub.current_version})
    db.commit()
    return {"ok": True, "status": "submitted", "version": sub.current_version, "submitted_at": sub.submitted_at.isoformat()}


# ---------- Medien ----------


def _serialize_media(a: MediaAsset) -> dict:
    return {
        "id": a.id,
        "orig_name": a.orig_name,
        "filename": media_name(a.id, a.orig_name),
        "mime": a.mime,
        "size_bytes": a.size_bytes,
        "sha256": a.sha256,
        "license": a.license,
        "license_text": a.license_text,
        "source": a.source,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("/play/media")
def list_media(p: Project = Depends(get_student_project), db: Session = Depends(get_db)):
    rows = db.query(MediaAsset).filter_by(project_id=p.id).order_by(MediaAsset.id).all()
    return {"media": [_serialize_media(a) for a in rows], "license_choices": LICENSE_CHOICES}


def _update_editor_media(db, p, name, content):
    save = db.get(Save, p.id)
    data = json.loads(save.payload) if save else {}
    if data.get("files") is None:
        return None
    files = data["files"]
    if content is None:
        files.pop(name, None)
    else:
        files[name] = base64.b64encode(content).decode()
    data = save_payload(data["source"], data.get("db"), files)
    store_save(db, p, json.dumps(data).encode(), p.revision)
    return SaveIn(source=data["source"], db=data.get("db"), files=data["files"])


@router.post("/play/media")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    license: str = Form(""),
    license_text: str = Form(""),
    source: str = Form(""),
    p: Project = Depends(get_student_project),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    require_writable(db, p)
    if not request.app.state.rate_limiter.allow(f"media:{p.id}", 30, 60):
        raise HTTPException(429, "Zu viele Uploads")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_MEDIA:
        raise HTTPException(400, f"Dateityp nicht erlaubt: {ext or '(keine Endung)'} — erlaubt: {', '.join(sorted(ALLOWED_MEDIA))}")
    mime = ALLOWED_MEDIA[ext][0]
    head = await file.read(16)
    if not check_media_head(head, ext):
        raise HTTPException(400, "Dateiinhalt passt nicht zum Typ (Magic-Bytes-Prüfung)")
    content = head + await file.read(MAX_MEDIA_FILE_BYTES + 1)
    if len(content) > MAX_MEDIA_FILE_BYTES:
        raise HTTPException(413, f"Datei zu groß (max {MAX_MEDIA_FILE_BYTES // 1048576} MB)")
    used = compute_used_bytes(db, p)
    if used + len(content) > p.quota_bytes:
        raise HTTPException(413, "Quota überschritten durch Medien-Upload")
    original = re.sub(r"[\r\n\t]", "", os.path.basename(file.filename or "datei"))[:255]
    existing = db.query(MediaAsset).filter_by(project_id=p.id).all()
    if any(media_name(a.id, a.orig_name) == media_name(0, original) for a in existing):
        raise HTTPException(409, "Eine Datei mit diesem Namen ist bereits vorhanden. Bitte benenne die neue Datei um.")
    asset = MediaAsset(
        project_id=p.id,
        orig_name=original,
        mime=mime,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        license=license[:64],
        license_text=license_text[:2000],
        source=source[:2000],
    )
    db.add(asset)
    db.flush()
    asset.stored_name = f"{asset.id}{ext}"
    db.flush()
    editor_save = _update_editor_media(db, p, media_name(asset.id, asset.orig_name), content)
    target_dir = project_media_dir(settings, p.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / asset.stored_name).write_bytes(content)
    db.commit()
    try:
        if editor_save:
            _commit_save_to_git(db, settings, p, editor_save)
        else:
            gitstore.commit_media(settings, p.id, f"Medien hochgeladen: {asset.orig_name}")
    except gitstore.GitError as error:
        log_audit(db, "code", f"project:{p.id}", "git_commit_failed", meta={"error": str(error)})
        db.commit()
    return {"ok": True, "media": _serialize_media(asset)}


class MediaPatchIn(BaseModel):
    license: str | None = None
    license_text: str | None = None
    source: str | None = None


@router.patch("/play/media/{asset_id}")
def patch_media(asset_id: int, body: MediaPatchIn, p: Project = Depends(get_student_project), db: Session = Depends(get_db)):
    a = db.get(MediaAsset, asset_id)
    if not a or a.project_id != p.id:
        raise HTTPException(404, "Medium nicht gefunden")
    require_writable(db, p)
    if body.license is not None:
        a.license = body.license[:64]
    if body.license_text is not None:
        a.license_text = body.license_text[:2000]
    if body.source is not None:
        a.source = body.source[:2000]
    db.commit()
    return {"ok": True, "media": _serialize_media(a)}


@router.delete("/play/media/{asset_id}")
def delete_media(asset_id: int, p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    a = db.get(MediaAsset, asset_id)
    if not a or a.project_id != p.id:
        raise HTTPException(404, "Medium nicht gefunden")
    require_writable(db, p)
    path = project_media_dir(settings, p.id) / a.stored_name
    db.delete(a)
    db.flush()
    editor_save = _update_editor_media(db, p, media_name(a.id, a.orig_name), None)
    db.commit()
    path.unlink(missing_ok=True)
    try:
        if editor_save:
            _commit_save_to_git(db, settings, p, editor_save)
        else:
            gitstore.commit_media(settings, p.id, f"Medien gelöscht: {a.orig_name}")
    except gitstore.GitError as error:
        log_audit(db, "code", f"project:{p.id}", "git_commit_failed", meta={"error": str(error)})
        db.commit()
    return {"ok": True, "used_bytes": compute_used_bytes(db, p)}


@router.get("/play/media/{asset_id}/file")
def media_file(asset_id: int, p: Project = Depends(get_student_project), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    a = db.get(MediaAsset, asset_id)
    if not a or a.project_id != p.id:
        raise HTTPException(404, "Medium nicht gefunden")
    save = db.get(Save, p.id)
    files = json.loads(save.payload).get("files") if save else None
    if files is not None:
        content = files.get(media_name(a.id, a.orig_name))
        if content is None:
            raise HTTPException(404, "Medium nicht gefunden")
        return Response(base64.b64decode(content), media_type=a.mime, headers={"X-Content-Type-Options": "nosniff"})
    path = project_media_dir(settings, p.id) / a.stored_name
    if not path.exists():
        raise HTTPException(404, "Datei fehlt auf dem Datenträger")
    return FileResponse(path, media_type=a.mime, filename=a.orig_name, headers={"X-Content-Type-Options": "nosniff"})
