from __future__ import annotations

import json
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import log_audit
from ..deps import get_db, require_admin, require_csrf, require_teacher
from ..models import PublicTask, Task, TaskItem, User, utcnow
from ..task_data import information_items

router = APIRouter(prefix="/api/teacher", tags=["gallery"], dependencies=[Depends(require_teacher), Depends(require_csrf)])
admin_router = APIRouter(prefix="/api/admin", tags=["admin-gallery"], dependencies=[Depends(require_admin), Depends(require_csrf)])

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,59}$")
TASK_LICENSES = ["plattform-intern (nur kopieren)", "CC BY", "CC BY-SA", "CC0"]


def _owned_task(db: Session, teacher: User, tid: int) -> Task:
    t = db.get(Task, tid)
    if not t or t.teacher_id != teacher.id:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    return t


def _serialize_public(db: Session, pt: PublicTask, with_items: bool = False) -> dict:
    d = {
        "id": pt.id,
        "task_id": pt.task_id,
        "slug": pt.slug,
        "version": pt.version,
        "title": pt.title,
        "description": pt.description,
        "author_alias": pt.author_alias,
        "school": pt.school,
        "license": pt.license,
        "status": pt.status,
        "published_at": pt.published_at.isoformat() if pt.published_at else None,
        "items_count": len(json.loads(pt.items)),
    }
    if with_items:
        d["items"] = information_items(json.loads(pt.items))
    return d


class PublishIn(BaseModel):
    author_alias: str | None = None
    license: str | None = None
    slug: str | None = None


@router.post("/tasks/{tid}/publish")
def publish_task(tid: int, body: PublishIn, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    """Snapshot der Aufgabendefinition öffentlich in der Galerie. Niemals Abgaben/Antworten."""
    t = _owned_task(db, teacher, tid)
    items = [
        {"kind": i.kind, "prompt": i.prompt, "position": i.position}
        for i in sorted(t.items, key=lambda i: i.position)
    ]
    existing = db.query(PublicTask).filter_by(task_id=t.id).first()
    if existing:
        # Re-Publish (auch nach unpublish): gleicher Datensatz, neue Version, gleicher Slug
        existing.status = "published"
        existing.version += 1
        existing.title = t.title
        existing.description = t.description
        existing.items = json.dumps(items, ensure_ascii=False).encode()
        existing.author_alias = (body.author_alias or existing.author_alias or "")[:128]
        existing.license = (body.license or existing.license)[:64]
        existing.published_at = utcnow()
        pt = existing
    else:
        slug = (body.slug or "").strip().lower()
        if not slug:
            slug = f"aufgabe-{t.id}-{secrets.token_hex(3)}"
        if not SLUG_RE.match(slug):
            raise HTTPException(400, "Slug: nur a-z, 0-9, '-', 3-60 Zeichen")
        if db.query(PublicTask).filter_by(slug=slug).first():
            raise HTTPException(409, "Slug bereits vergeben")
        pt = PublicTask(
            task_id=t.id,
            slug=slug,
            version=1,
            title=t.title,
            description=t.description,
            items=json.dumps(items, ensure_ascii=False).encode(),
            author_alias=(body.author_alias or "")[:128],
            school=teacher.school,
            license=(body.license or TASK_LICENSES[0])[:64],
            status="published",
            published_by=teacher.id,
        )
        db.add(pt)
    log_audit(db, "teacher", f"user:{teacher.id}", "task_published", target=f"task:{tid}", meta={"public_task": pt.id, "version": pt.version})
    db.commit()
    return {"public_task": _serialize_public(db, pt)}


@router.get("/my-public-tasks")
def my_public_tasks(teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    rows = db.query(PublicTask).filter_by(published_by=teacher.id).order_by(PublicTask.id.desc()).all()
    return {"public_tasks": [_serialize_public(db, r) for r in rows]}


@router.post("/public-tasks/{pt_id}/unpublish")
def unpublish(pt_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    pt = db.get(PublicTask, pt_id)
    if not pt or pt.published_by != teacher.id:
        raise HTTPException(404, "Nicht gefunden")
    pt.status = "hidden"
    log_audit(db, "teacher", f"user:{teacher.id}", "task_unpublished", target=f"public_task:{pt_id}")
    db.commit()
    return {"ok": True}


@router.get("/gallery")
def gallery(q: str = "", db: Session = Depends(get_db)):
    query = db.query(PublicTask).filter_by(status="published")
    if q:
        query = query.filter(PublicTask.title.contains(q))
    rows = query.order_by(PublicTask.published_at.desc()).limit(200).all()
    return {"tasks": [_serialize_public(db, r) for r in rows], "license_choices": TASK_LICENSES}


@router.get("/gallery/{pt_id}")
def gallery_detail(pt_id: int, db: Session = Depends(get_db)):
    pt = db.get(PublicTask, pt_id)
    if not pt or pt.status != "published":
        raise HTTPException(404, "Nicht gefunden")
    return {"task": _serialize_public(db, pt, with_items=True)}


@router.post("/gallery/{pt_id}/copy")
def copy_public_task(pt_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    """Kopie einer öffentlichen Aufgabe in den eigenen Bestand (unabhängig, ohne Abgaben)."""
    pt = db.get(PublicTask, pt_id)
    if not pt or pt.status != "published":
        raise HTTPException(404, "Nicht gefunden")
    items = information_items(json.loads(pt.items))
    t = Task(
        teacher_id=teacher.id,
        title=pt.title[:255],
        description=pt.description,
        is_template_for_new_projects=False,
        source_public_task_id=pt.id,
    )
    db.add(t)
    db.flush()
    for pos, item in enumerate(sorted(items, key=lambda x: x.get("position", 0))):
        db.add(TaskItem(task_id=t.id, position=item.get("position", pos), kind=item.get("kind", "text"), prompt=item.get("prompt", "")))
    log_audit(db, "teacher", f"user:{teacher.id}", "public_task_copied", target=f"public_task:{pt_id}", meta={"new_task": t.id})
    db.commit()
    return {"ok": True, "task_id": t.id, "title": t.title}


# ---------- Admin: Moderation ----------


@admin_router.get("/public-tasks")
def admin_public_tasks(db: Session = Depends(get_db)):
    rows = db.query(PublicTask).order_by(PublicTask.id.desc()).all()
    return {"public_tasks": [_serialize_public(db, r) for r in rows]}


class HideIn(BaseModel):
    hidden: bool


@admin_router.post("/public-tasks/{pt_id}/hide")
def admin_hide(pt_id: int, body: HideIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    pt = db.get(PublicTask, pt_id)
    if not pt:
        raise HTTPException(404, "Nicht gefunden")
    pt.status = "hidden" if body.hidden else "published"
    log_audit(db, "admin", f"user:{admin.id}", "public_task_hidden" if body.hidden else "public_task_unhidden", target=f"public_task:{pt_id}", meta={"title": pt.title})
    db.commit()
    return {"ok": True, "status": pt.status}
