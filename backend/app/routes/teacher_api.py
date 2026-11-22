from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from .. import gitstore
from ..archives import project_snapshot, project_zip, unpack_snapshot
from ..projects import assign_templates, copy_project_content, new_project, owned_course, set_read_only
from ..task_data import checkbox_answers
from ..audit import log_audit
from ..config import Settings
from ..deps import get_db, get_settings, require_csrf, require_teacher
from ..models import (
    AuditLog,
    Course,
    MediaAsset,
    Project,
    ProjectRemote,
    Save,
    ShareRequest,
    Submission,
    SubmissionVersion,
    Task,
    TaskAssignment,
    TaskItem,
    User,
    Workspace,
    TemplateCode,
    aware,
    utcnow,
)
from ..security import decrypt_code, encrypt_code, encrypt_secret, gen_code, hash_code
from ..storage import storage_policy
from ..services import (
    compute_used_bytes,
    decode_answers,
    default_quota,
    delete_project_cascade,
    project_media_dir,
    quota_cap,
    serialize_project,
)
from pathlib import Path

router = APIRouter(prefix="/api/teacher", tags=["teacher"], dependencies=[Depends(require_teacher), Depends(require_csrf)])


def _owned_project(db: Session, teacher: User, pid: int) -> Project:
    p = db.get(Project, pid)
    if not p or p.teacher_id != teacher.id:
        raise HTTPException(404, "Projekt nicht gefunden")
    return p


def _owned_task(db: Session, teacher: User, tid: int) -> Task:
    t = db.get(Task, tid)
    if not t or t.teacher_id != teacher.id:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    return t


def _owned_submission(db: Session, teacher: User, sid: int) -> Submission:
    sub = db.get(Submission, sid)
    if not sub:
        raise HTTPException(404, "Abgabe nicht gefunden")
    p = db.get(Project, sub.project_id)
    if not p or p.teacher_id != teacher.id:
        raise HTTPException(404, "Abgabe nicht gefunden")
    return sub


# ---------- Projekte / Codes ----------

@router.get("/me")
def me(teacher: User = Depends(require_teacher)):
    return {"id": teacher.id, "email": teacher.email, "school": teacher.school, "role": teacher.role}


class ProjectCreateIn(BaseModel):
    count: int = Field(default=1, ge=1, le=200)
    course_id: int | None = None
    template_project_id: int | None = None
    access_mode: str = Field(default="project", pattern="^(project|template_once)$")
    code_readonly_days: int | None = Field(default=365, ge=1, le=36500)
    code_expires_at: datetime | None = None
    writable_until: datetime | None = None


def utc_date(value):
    if value is not None and value.tzinfo is None:
        raise HTTPException(422, "Datumsangaben müssen eine Zeitzone enthalten.")
    return value.astimezone(timezone.utc) if value else None


@router.post("/projects")
def create_projects(body: ProjectCreateIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Erzeugt Projekt-Codes. Klartext-Codes werden nur einmalig zurückgegeben (später: GET /projects/{id}/code)."""
    count = body.count
    owned_course(db, teacher.id, body.course_id)
    if body.access_mode == "template_once":
        if body.template_project_id is None:
            raise HTTPException(422, "Bitte ein Startprojekt auswählen.")
        source = _owned_project(db, teacher, body.template_project_id)
        if body.course_id is not None and body.course_id != source.course_id:
            raise HTTPException(422, "Vorlagencodes verwenden die Klasse des Startprojekts. Bitte diese Klasse auswählen.")
        out = []
        for _ in range(count):
            code = gen_code(16)
            row = TemplateCode(project_id=source.id, code_hash=hash_code(code), code_enc=encrypt_code(code, settings.secret_key), expires_at=utc_date(body.code_expires_at))
            db.add(row)
            db.flush()
            out.append({"id": row.id, "code": code})
        db.commit()
        return {"projects": out, "access_mode": "template_once"}
    snapshot, template_tasks = None, []
    if body.template_project_id is not None:
        source = _owned_project(db, teacher, body.template_project_id)
        snapshot = project_snapshot(db, settings, source)
        # Vor dem Kopieren auf Vollständigkeit und verfügbare Projektquota prüfen.
        payload_size = len(json.dumps(snapshot["save"]).encode()) if snapshot["save"] is not None else 0
        media_size = sum(a.size_bytes for a in db.query(MediaAsset).filter_by(project_id=source.id))
        if payload_size + media_size > default_quota(db, settings):
            raise HTTPException(413, "Das Startprojekt überschreitet den Speicherplatz für neue Projekte. Bitte verkleinern oder die Standardquota erhöhen.")
        for task in db.query(Task).join(TaskAssignment).filter(TaskAssignment.project_id == source.id).all():
            if task.course_id in (None, body.course_id):
                template_tasks.append(task)
            else:
                clone = Task(teacher_id=teacher.id, course_id=body.course_id, title=task.title,
                             description=task.description, is_template_for_new_projects=False)
                clone.items = [TaskItem(kind=i.kind, prompt=i.prompt, position=i.position) for i in task.items]
                db.add(clone)
                db.flush()
                template_tasks.append(clone)
    out = []
    created_ids = []
    try:
        for _ in range(count):
            p, code = new_project(db, settings, teacher.id, body.course_id,
                                  title=source.title if snapshot else "Mein Projekt")
            created_ids.append(p.id)
            p.code_readonly_days = body.code_readonly_days if "code_readonly_days" in body.model_fields_set else settings.code_readonly_days
            p.code_expires_at = utc_date(body.code_expires_at)
            p.writable_until = utc_date(body.writable_until)
            if snapshot:
                copy_project_content(db, settings, p, snapshot)
                for task in template_tasks:
                    if not db.query(TaskAssignment).filter_by(task_id=task.id, project_id=p.id).first():
                        assignment = TaskAssignment(task_id=task.id, project_id=p.id)
                        db.add(assignment)
                        db.flush()
                        db.add(Submission(assignment_id=assignment.id, project_id=p.id))
            out.append({"id": p.id, "code": code})
        log_audit(db, "teacher", f"user:{teacher.id}", "projects_created", target=str(count))
        db.commit()
    except Exception:
        db.rollback()
        from ..services import delete_project_files
        for pid in created_ids:
            delete_project_files(settings, pid)
        raise
    return {"projects": out}


@router.get("/projects")
def list_projects(course_id: int | None = None, with_code: bool = False, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    query = db.query(Project).filter_by(teacher_id=teacher.id)
    if course_id is not None:
        owned_course(db, teacher.id, course_id)
        query = query.filter_by(course_id=course_id)
    rows = query.order_by(Project.id).all()
    return {"projects": [serialize_project(db, p, settings, with_code) for p in rows], "storage_policy": storage_policy(settings),
            "code_defaults": {"readonly_days": settings.code_readonly_days}}


class CourseIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    school_year: str = Field(default="", max_length=32)


@router.get("/courses")
def list_courses(teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return {"courses": [{"id": c.id, "title": c.title, "school_year": c.school_year, "archived": c.archived,
                         "projects": db.query(Project).filter_by(course_id=c.id).count()}
                        for c in db.query(Course).filter_by(teacher_id=teacher.id).order_by(Course.id)]}


@router.post("/courses")
def create_course(body: CourseIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    if not body.title.strip():
        raise HTTPException(422, "Bitte eine Klassenbezeichnung eingeben")
    c = Course(teacher_id=teacher.id, title=body.title.strip(), school_year=body.school_year.strip())
    db.add(c)
    db.flush()
    log_audit(db, "teacher", f"user:{teacher.id}", "course_created", target=f"course:{c.id}")
    db.commit()
    return {"id": c.id}


class CoursePatchIn(BaseModel):
    archived: bool


@router.patch("/courses/{cid}")
def archive_course(cid: int, body: CoursePatchIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    c = owned_course(db, teacher.id, cid)
    if body.archived and not c.archived:
        c.archived_at = utcnow()
    elif not body.archived:
        c.archived_at = None
    c.archived = body.archived
    db.query(Project).filter_by(course_id=c.id).update({Project.revision: Project.revision + 1}, synchronize_session=False)
    log_audit(db, "teacher", f"user:{teacher.id}", "course_archived" if body.archived else "course_reactivated", target=f"course:{cid}")
    db.commit()
    return {"ok": True}


class ProjectBulkIn(BaseModel):
    project_ids: list[int] = Field(min_length=1, max_length=200)
    read_only: bool | None = None
    course_id: int | None = None


@router.patch("/projects/bulk")
def bulk_projects(body: ProjectBulkIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    rows = [_owned_project(db, teacher, pid) for pid in set(body.project_ids)]
    if "course_id" in body.model_fields_set:
        owned_course(db, teacher.id, body.course_id)
    for p in rows:
        p.revision += 1
        if body.read_only is not None:
            set_read_only(p, body.read_only)
        if "course_id" in body.model_fields_set:
            p.course_id = body.course_id
            assign_templates(db, p)
    log_audit(db, "teacher", f"user:{teacher.id}", "projects_bulk_updated", meta={"projects": [p.id for p in rows]})
    db.commit()
    return {"ok": True, "count": len(rows)}


@router.get("/projects/{pid}")
def project_detail(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    p = _owned_project(db, teacher, pid)
    save = db.get(Save, p.id)
    assignments = db.query(TaskAssignment).filter_by(project_id=p.id).all()
    return {
        **serialize_project(db, p),
        "save": json.loads(save.payload) if save else None,
        "assignments": [
            {"assignment_id": a.id, "task_id": a.task_id, "task_title": db.get(Task, a.task_id).title if db.get(Task, a.task_id) else None}
            for a in assignments
        ],
    }


@router.get("/projects/{pid}/code")
def project_code(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    p = _owned_project(db, teacher, pid)
    return {"id": p.id, "code": decrypt_code(p.code_enc, settings.secret_key)}


@router.get("/projects/{pid}/snapshot")
def preview_project(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return {"snapshot": project_snapshot(db, settings, _owned_project(db, teacher, pid))}


@router.get("/projects/{pid}/download")
def download_project(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    data = project_snapshot(db, settings, _owned_project(db, teacher, pid))
    return Response(content=project_zip(data), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="projekt-{pid}.zip"'})


class ProjectPatchIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    course_id: int | None = None
    quota_bytes: int | None = None
    read_only: bool | None = None
    writable_until: datetime | None = None
    code_expires_at: datetime | None = None
    code_readonly_days: int | None = Field(default=None, ge=1, le=36500)


@router.patch("/projects/{pid}")
def patch_project(pid: int, body: ProjectPatchIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    p = _owned_project(db, teacher, pid)
    changes: dict = {}
    if "course_id" in body.model_fields_set:
        owned_course(db, teacher.id, body.course_id)
        p.course_id = body.course_id
        p.revision += 1
        assign_templates(db, p)
        changes["course_id"] = p.course_id
    if body.title is not None:
        if not body.title.strip():
            raise HTTPException(422, "Bitte einen Projekttitel eingeben")
        p.title = body.title.strip()
        changes["title"] = p.title
    if body.quota_bytes is not None:
        cap = quota_cap(db, settings)
        if body.quota_bytes <= 0 or body.quota_bytes > cap:
            raise HTTPException(400, f"Quota muss zwischen 1 und {cap} Bytes liegen (Admin-Cap)")
        p.quota_bytes = body.quota_bytes
        changes["quota_bytes"] = body.quota_bytes
    if body.read_only is not None:
        p.revision += 1
        set_read_only(p, body.read_only)
        changes["read_only"] = body.read_only
    for name in ("writable_until", "code_expires_at", "code_readonly_days"):
        if name in body.model_fields_set:
            value = getattr(body, name)
            setattr(p, name, utc_date(value) if name.endswith("_at") or name == "writable_until" else value)
            p.revision += 1
    log_audit(db, "teacher", f"user:{teacher.id}", "project_updated", target=f"project:{pid}", meta=changes)
    db.commit()
    return {"ok": True, "project": serialize_project(db, p), "changes": changes}


@router.get("/template-codes")
def template_codes(teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = db.query(TemplateCode).join(Project).filter(Project.teacher_id == teacher.id).order_by(TemplateCode.id.desc()).all()
    return {"codes": [{"id": r.id, "project_id": r.project_id, "code": decrypt_code(r.code_enc, settings.secret_key), "used_at": aware(r.used_at), "expires_at": aware(r.expires_at)} for r in rows]}


@router.delete("/template-codes/{cid}")
def revoke_template_code(cid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    row = db.get(TemplateCode, cid)
    if not row:
        raise HTTPException(404, "Code nicht gefunden")
    _owned_project(db, teacher, row.project_id)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.delete("/projects/{pid}/password")
def reset_student_password(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    p = _owned_project(db, teacher, pid)
    workspace = db.get(Workspace, p.workspace_id)
    workspace.password_hash = None
    workspace.credential_version += 1
    log_audit(db, "teacher", f"user:{teacher.id}", "student_password_reset", target=f"project:{pid}")
    db.commit()
    return {"ok": True}


class RemoteIn(BaseModel):
    url: str
    token: str | None = None  # leer = ohne Auth; verschlüsselt at rest, nie zurückgegeben


@router.get("/projects/{pid}/remote")
def project_get_remote(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Remote des Projekts (URL + ob ein Token hinterlegt ist — nie das Token selbst)."""
    p = _owned_project(db, teacher, pid)
    row = db.get(ProjectRemote, p.id)
    url = row.url if row else gitstore.remote_url(settings, p.id)
    return {"configured": bool(url), "url": url, "has_token": bool(row and row.token_enc)}


@router.put("/projects/{pid}/remote")
def project_put_remote(pid: int, body: RemoteIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Remote für ein Projekt setzen (z. B. Klassen-Repo auf GitHub mit PAT) — Schüler pushen dann per Klick."""
    p = _owned_project(db, teacher, pid)
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
    log_audit(db, "teacher", f"user:{teacher.id}", "git_remote_set", target=f"project:{pid}", meta={"url": url, "has_token": bool(token)})
    db.commit()
    return {"ok": True, "url": url, "has_token": bool(token)}


@router.delete("/projects/{pid}/remote")
def project_delete_remote(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    p = _owned_project(db, teacher, pid)
    gitstore.remove_remote(settings, p.id)
    row = db.get(ProjectRemote, p.id)
    if row:
        db.delete(row)
    log_audit(db, "teacher", f"user:{teacher.id}", "git_remote_removed", target=f"project:{pid}")
    db.commit()
    return {"ok": True}


@router.post("/projects/{pid}/regenerate-code")
def regenerate_code(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Code-Wechsel nach Leak: alter Code und alle Schüler-Tokens werden sofort ungültig."""
    p = _owned_project(db, teacher, pid)
    # Ein Code öffnet alle Projekte desselben namenlosen Arbeitsbereichs.
    # Bei einem Leak deshalb sämtliche dort ausgestellten Tokens widerrufen.
    siblings = db.query(Project).filter_by(workspace_id=p.workspace_id).all() if p.workspace_id else [p]
    code = ""
    for sibling in siblings:
        new_code = gen_code(10)
        sibling.code_hash = hash_code(new_code)
        sibling.code_enc = encrypt_code(new_code, settings.secret_key)
        if sibling.id == p.id:
            code = new_code
    log_audit(db, "teacher", f"user:{teacher.id}", "code_regenerated", target=f"project:{pid}")
    db.commit()
    return {"id": p.id, "code": code}


@router.delete("/projects/{pid}")
def delete_project(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    p = _owned_project(db, teacher, pid)
    delete_project_cascade(db, settings, p)
    log_audit(db, "teacher", f"user:{teacher.id}", "project_deleted", target=f"project:{pid}")
    db.commit()
    return {"ok": True}


@router.post("/projects/{pid}/fork")
def fork_project(pid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """„Sofort starten“: erzeugt eine Kopie des Schüler-Projekts (Save + Medien). Original bleibt unangetastet."""
    src = _owned_project(db, teacher, pid)
    p, code = new_project(db, settings, teacher.id, title=f"Kopie von {src.title}"[:120])
    old_save = db.get(Save, src.id)
    if old_save:
        db.add(Save(project_id=p.id, payload=old_save.payload, size_bytes=old_save.size_bytes))
    src_dir = project_media_dir(settings, src.id)
    dst_dir = project_media_dir(settings, p.id)
    for a in db.query(MediaAsset).filter_by(project_id=src.id).all():
        db.add(
            MediaAsset(
                project_id=p.id,
                stored_name=a.stored_name,
                orig_name=a.orig_name,
                mime=a.mime,
                size_bytes=a.size_bytes,
                sha256=a.sha256,
                license=a.license,
                license_text=a.license_text,
                source=a.source,
            )
        )
        db.flush()
        new = db.query(MediaAsset).filter_by(project_id=p.id).order_by(MediaAsset.id.desc()).first()
        new.stored_name = f"{new.id}{Path(a.stored_name).suffix}"
        src_file = src_dir / a.stored_name
        if src_file.exists():
            dst_dir.mkdir(parents=True, exist_ok=True)
            (dst_dir / new.stored_name).write_bytes(src_file.read_bytes())
    db.flush()
    log_audit(db, "teacher", f"user:{teacher.id}", "project_forked", target=f"project:{pid}", meta={"fork": p.id})
    db.commit()
    return {"id": p.id, "code": code}


# ---------- Excel/CSV-Export (nur Codes — Namen bleiben lokal beim Lehrer) ----------


def _export_rows(db: Session, teacher: User, settings: Settings) -> list[list]:
    header = ["Code", "Projekt-ID", "Erstellt", "Quota-Bytes", "Genutzt-Bytes", "Read-Only", "Öffentlich (Slug)", "Aufgaben zugewiesen"]
    rows = [header]
    for p in db.query(Project).filter_by(teacher_id=teacher.id).order_by(Project.id).all():
        sr = db.query(ShareRequest).filter_by(project_id=p.id, status="approved").order_by(ShareRequest.id.desc()).first()
        rows.append(
            [
                decrypt_code(p.code_enc, settings.secret_key),
                p.id,
                p.created_at.isoformat() if p.created_at else "",
                p.quota_bytes,
                compute_used_bytes(db, p),
                "ja" if p.read_only else "nein",
                sr.slug if sr and sr.slug else "",
                db.query(TaskAssignment).filter_by(project_id=p.id).count(),
            ]
        )
    return rows


@router.get("/projects.xlsx")
def projects_xlsx(teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    import io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Codes"
    for row in _export_rows(db, teacher, settings):
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="miniworlds-codes.xlsx"'},
    )


@router.get("/projects.csv")
def projects_csv(teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    for row in _export_rows(db, teacher, settings):
        w.writerow(row)
    return Response(
        content=buf.getvalue().encode(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="miniworlds-codes.csv"'},
    )


# ---------- Aufgaben ----------

class TaskIn(BaseModel):
    course_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    is_template_for_new_projects: bool = False


@router.post("/tasks")
def create_task(body: TaskIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    owned_course(db, teacher.id, body.course_id)
    if not body.title.strip():
        raise HTTPException(422, "Bitte einen Titel eingeben")
    t = Task(teacher_id=teacher.id, course_id=body.course_id, title=body.title.strip(), description=body.description, is_template_for_new_projects=body.is_template_for_new_projects)
    db.add(t)
    db.flush()
    log_audit(db, "teacher", f"user:{teacher.id}", "task_created", target=f"task:{t.id}", meta={"title": t.title})
    db.commit()
    return {"task": _serialize_task(db, t)}


@router.get("/tasks")
def list_tasks(teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    rows = db.query(Task).filter_by(teacher_id=teacher.id).order_by(Task.id).all()
    return {"tasks": [_serialize_task(db, t) for t in rows]}


@router.get("/tasks/{tid}")
def task_detail(tid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    t = _owned_task(db, teacher, tid)
    d = _serialize_task(db, t)
    d["assignments"] = [a.project_id for a in db.query(TaskAssignment).filter_by(task_id=t.id).all()]
    return {"task": d}


class TaskPatchIn(BaseModel):
    title: str | None = None
    description: str | None = None
    is_template_for_new_projects: bool | None = None


@router.patch("/tasks/{tid}")
def patch_task(tid: int, body: TaskPatchIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    t = _owned_task(db, teacher, tid)
    changes = {}
    if body.title is not None:
        if not body.title.strip() or len(body.title) > 255:
            raise HTTPException(422, "Titel muss 1 bis 255 Zeichen enthalten")
        t.title = body.title.strip()
        changes["title"] = t.title
    if body.description is not None:
        t.description = body.description
        changes["description"] = body.description
    if body.is_template_for_new_projects is not None:
        t.is_template_for_new_projects = body.is_template_for_new_projects
        changes["is_template_for_new_projects"] = t.is_template_for_new_projects
    t.updated_at = utcnow()
    log_audit(db, "teacher", f"user:{teacher.id}", "task_updated", target=f"task:{tid}", meta=changes)
    db.commit()
    return {"task": _serialize_task(db, t)}


@router.delete("/tasks/{tid}")
def delete_task(tid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    t = _owned_task(db, teacher, tid)
    for a in db.query(TaskAssignment).filter_by(task_id=t.id).all():
        for sub in db.query(Submission).filter_by(assignment_id=a.id).all():
            db.query(SubmissionVersion).filter_by(submission_id=sub.id).delete()
            db.delete(sub)
        db.delete(a)
    db.query(TaskItem).filter_by(task_id=t.id).delete()
    db.delete(t)
    log_audit(db, "teacher", f"user:{teacher.id}", "task_deleted", target=f"task:{tid}")
    db.commit()
    return {"ok": True}


class ItemIn(BaseModel):
    kind: str  # text | checkbox
    prompt: str
    position: int | None = None


@router.post("/tasks/{tid}/items")
def add_item(tid: int, body: ItemIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    t = _owned_task(db, teacher, tid)
    if body.kind not in ("text", "checkbox"):
        raise HTTPException(400, "Nur Informationstext und Checkbox sind erlaubt")
    if body.position is None:
        maxpos = db.query(TaskItem).filter_by(task_id=t.id).count()
        body.position = maxpos
    item = TaskItem(task_id=t.id, kind=body.kind, prompt=body.prompt, position=body.position)
    db.add(item)
    t.updated_at = utcnow()
    db.commit()
    return {"item": {"id": item.id, "kind": item.kind, "prompt": item.prompt, "position": item.position}}


class ItemPatchIn(BaseModel):
    kind: str | None = None
    prompt: str | None = None
    position: int | None = None


@router.patch("/tasks/{tid}/items/{iid}")
def patch_item(tid: int, iid: int, body: ItemPatchIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _owned_task(db, teacher, tid)
    item = db.get(TaskItem, iid)
    if not item or item.task_id != tid:
        raise HTTPException(404, "Item nicht gefunden")
    if body.kind is not None:
        if body.kind not in ("text", "checkbox"):
            raise HTTPException(400, "Nur Informationstext und Checkbox sind erlaubt")
        item.kind = body.kind
    if body.prompt is not None:
        item.prompt = body.prompt
    if body.position is not None:
        item.position = body.position
    db.commit()
    return {"item": {"id": item.id, "kind": item.kind, "prompt": item.prompt, "position": item.position}}


@router.delete("/tasks/{tid}/items/{iid}")
def delete_item(tid: int, iid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _owned_task(db, teacher, tid)
    item = db.get(TaskItem, iid)
    if not item or item.task_id != tid:
        raise HTTPException(404, "Item nicht gefunden")
    db.delete(item)
    db.commit()
    return {"ok": True}


class AssignIn(BaseModel):
    project_ids: list[int] | None = None
    all: bool = False


@router.post("/tasks/{tid}/assign")
def assign_task(tid: int, body: AssignIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    t = _owned_task(db, teacher, tid)
    if body.all:
        t.is_template_for_new_projects = True
        query = db.query(Project).filter_by(teacher_id=teacher.id)
        if t.course_id is not None:
            query = query.filter_by(course_id=t.course_id)
        targets = query.all()
    else:
        targets = []
        for pid in body.project_ids or []:
            targets.append(_owned_project(db, teacher, pid))
    created = 0
    for p in targets:
        exists = db.query(TaskAssignment).filter_by(task_id=t.id, project_id=p.id).first()
        if exists:
            continue
        a = TaskAssignment(task_id=t.id, project_id=p.id)
        db.add(a)
        db.flush()
        db.add(Submission(assignment_id=a.id, project_id=p.id))
        created += 1
    log_audit(db, "teacher", f"user:{teacher.id}", "task_assigned", target=f"task:{tid}", meta={"created": created, "all": body.all})
    db.commit()
    return {"created": created}


@router.get("/tasks/{tid}/submissions")
def task_submissions(tid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    t = _owned_task(db, teacher, tid)
    out = []
    for a in db.query(TaskAssignment).filter_by(task_id=t.id).order_by(TaskAssignment.id).all():
        p = db.get(Project, a.project_id)
        sub = db.query(Submission).filter_by(assignment_id=a.id).first()
        out.append(
            {
                "assignment_id": a.id,
                "submission_id": sub.id if sub else None,
                "course_id": p.course_id if p else None,
                "project_title": p.title if p else "",
                "project_id": a.project_id,
                "code": decrypt_code(p.code_enc, settings.secret_key) if p else None,
                "status": sub.status if sub else "open",
                "submitted_at": sub.submitted_at.isoformat() if sub and sub.submitted_at else None,
                "done": sub.done if sub else False,
                "version": sub.current_version if sub else 0,
                "answers": decode_answers(db, sub),
            }
        )
    return {"task_id": tid, "submissions": out}


@router.get("/submissions/{sid}/versions")
def submission_versions(sid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    sub = _owned_submission(db, teacher, sid)
    return {"versions": [{"version": v.version, "created_at": v.created_at.isoformat(), "snapshot_available": v.project_snapshot is not None}
                         for v in db.query(SubmissionVersion).filter_by(submission_id=sub.id, submitted=True).order_by(SubmissionVersion.version.desc())]}


def _submission_version(db, teacher, sid, version):
    sub = _owned_submission(db, teacher, sid)
    v = db.query(SubmissionVersion).filter_by(submission_id=sub.id, version=version, submitted=True).first()
    if not v or not v.project_snapshot:
        raise HTTPException(404, "Für diese Abgabe ist kein eingefrorener Projektstand vorhanden")
    return v


@router.get("/submissions/{sid}/versions/{version}")
def submission_snapshot(sid: int, version: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    v = _submission_version(db, teacher, sid, version)
    return {"snapshot": unpack_snapshot(v.project_snapshot), "answers": checkbox_answers(json.loads(v.payload))}


@router.get("/submissions/{sid}/versions/{version}/download")
def submission_download(sid: int, version: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    v = _submission_version(db, teacher, sid, version)
    return Response(content=project_zip(unpack_snapshot(v.project_snapshot), json.loads(v.payload)), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="abgabe-{sid}-v{version}.zip"'})


@router.post("/submissions/{sid}/reopen")
def reopen_submission(sid: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    sub = _owned_submission(db, teacher, sid)
    if sub.status != "submitted":
        raise HTTPException(409, "Abgabe ist nicht eingereicht")
    sub.status = "open"
    sub.done = False
    log_audit(db, "teacher", f"user:{teacher.id}", "submission_reopened", target=f"submission:{sid}", meta={"project": sub.project_id})
    db.commit()
    return {"ok": True, "status": sub.status}


class SubmissionPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    done: bool | None = None


@router.patch("/submissions/{sid}")
def patch_submission(sid: int, body: SubmissionPatchIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    sub = _owned_submission(db, teacher, sid)
    changes = {}
    if body.done is not None:
        sub.done = body.done
        changes["done"] = body.done
    log_audit(db, "teacher", f"user:{teacher.id}", "submission_reviewed", target=f"submission:{sid}", meta=changes)
    db.commit()
    return {"ok": True, "status": sub.status, "done": sub.done}


@router.get("/export")
def export_own_data(teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """DSGVO-Selbstauskunft: alle eigenen Daten als JSON (keine Schüler-Namen — die existieren serverseitig nicht)."""
    projects = db.query(Project).filter_by(teacher_id=teacher.id).all()
    return {
        "user": {"id": teacher.id, "email": teacher.email, "school": teacher.school, "role": teacher.role, "created_at": teacher.created_at.isoformat()},
        "projects": [
            {
                "id": p.id,
                "created_at": p.created_at.isoformat(),
                "last_save_at": p.last_save_at.isoformat() if p.last_save_at else None,
                "quota_bytes": p.quota_bytes,
                "used_bytes": compute_used_bytes(db, p),
                "read_only": p.read_only,
                "save_size_bytes": (db.get(Save, p.id).size_bytes if db.get(Save, p.id) else 0),
                "media": [
                    {"id": m.id, "orig_name": m.orig_name, "mime": m.mime, "size_bytes": m.size_bytes, "license": m.license, "source": m.source}
                    for m in db.query(MediaAsset).filter_by(project_id=p.id).all()
                ],
                "tasks_assigned": db.query(TaskAssignment).filter_by(project_id=p.id).count(),
            }
            for p in projects
        ],
        "tasks": [
            {"id": t.id, "title": t.title, "created_at": t.created_at.isoformat(), "items": len(t.items)}
            for t in db.query(Task).filter_by(teacher_id=teacher.id).all()
        ],
    }


@router.get("/audit")
def teacher_audit(limit: int = 200, teacher: User = Depends(require_teacher), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.teacher_id == teacher.id, AuditLog.ts >= utcnow() - timedelta(days=settings.audit_retention_days))
        .order_by(AuditLog.id.desc())
        .limit(max(1, min(limit, 1000)))
        .all()
    )
    return {
        "entries": [
            {
                "id": r.id,
                "ts": r.ts.isoformat(),
                "actor_type": r.actor_type,
                "actor_ref": r.actor_ref,
                "action": r.action,
                "target": r.target,
                "meta": r.meta,
            }
            for r in reversed(rows)
        ]
    }


def _serialize_task(db: Session, t: Task) -> dict:
    return {
        "id": t.id,
        "course_id": t.course_id,
        "title": t.title,
        "description": t.description,
        "is_template_for_new_projects": t.is_template_for_new_projects,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "items": [
            {"id": i.id, "kind": i.kind, "prompt": i.prompt, "position": i.position}
            for i in sorted(t.items, key=lambda i: i.position)
        ],
        "assignments_count": db.query(TaskAssignment).filter_by(task_id=t.id).count(),
    }
