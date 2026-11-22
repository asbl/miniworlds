from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import log_audit
from ..config import Settings
from ..deps import get_db, get_settings, require_admin, require_csrf
from ..models import AuditLog, MediaAsset, Project, Save, Session as DbSession, Submission, SubmissionVersion, TaskAssignment, TeacherInvite, User, utcnow
from ..security import gen_code, hash_code
from ..services import serialize_project
from ..yearly import get_setting, set_setting

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin), Depends(require_csrf)])


# ---------- Lehrercodes (Invites) ----------

@router.get("/invites")
def list_invites(db: Session = Depends(get_db)):
    rows = db.query(TeacherInvite).order_by(TeacherInvite.id.desc()).all()
    return {
        "invites": [
            {
                "id": r.id,
                "school": r.school,
                "email": r.email,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "claimed_at": r.claimed_at.isoformat() if r.claimed_at else None,
            }
            for r in rows
        ]
    }


class InviteIn(BaseModel):
    school: str
    email: str | None = None
    expires_days: int | None = None


@router.post("/invites")
def create_invite(body: InviteIn, admin: User = Depends(require_admin), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Erzeugt einen Lehrercode. Der Klartext wird nur einmalig zurückgegeben."""
    code = gen_code(12)
    days = body.expires_days if body.expires_days is not None else settings.invite_expire_days
    inv = TeacherInvite(
        code_hash=hash_code(code),
        school=body.school.strip(),
        email=body.email.strip().lower() if body.email else None,
        created_by=admin.id,
        expires_at=utcnow() + timedelta(days=days) if days > 0 else None,
    )
    db.add(inv)
    db.flush()
    log_audit(db, "admin", f"user:{admin.id}", "invite_created", target=f"invite:{inv.id}", meta={"school": inv.school})
    db.commit()
    return {"id": inv.id, "code": code, "school": inv.school}


@router.delete("/invites/{invite_id}")
def delete_invite(invite_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    inv = db.get(TeacherInvite, invite_id)
    if not inv:
        raise HTTPException(404, "Invite nicht gefunden")
    if inv.claimed_at:
        raise HTTPException(409, "Invite wurde bereits eingelöst und kann nicht gelöscht werden")
    db.delete(inv)
    log_audit(db, "admin", f"user:{admin.id}", "invite_deleted", target=f"invite:{invite_id}")
    db.commit()
    return {"ok": True}


# ---------- Einstellungen ----------

@router.get("/settings")
def get_settings_api(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return {
        "teacher_quota_cap": int(get_setting(db, "teacher_quota_cap", str(settings.teacher_quota_cap))),
        "student_default_quota": int(get_setting(db, "student_default_quota", str(settings.default_quota_bytes))),
    }


class SettingsIn(BaseModel):
    teacher_quota_cap: int | None = None
    student_default_quota: int | None = None


@router.patch("/settings")
def patch_settings(body: SettingsIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    changes: dict = {}
    if body.teacher_quota_cap is not None:
        if body.teacher_quota_cap <= 0:
            raise HTTPException(400, "teacher_quota_cap muss > 0 sein")
        set_setting(db, "teacher_quota_cap", str(body.teacher_quota_cap))
        changes["teacher_quota_cap"] = body.teacher_quota_cap
    if body.student_default_quota is not None:
        if body.student_default_quota <= 0:
            raise HTTPException(400, "student_default_quota muss > 0 sein")
        set_setting(db, "student_default_quota", str(body.student_default_quota))
        changes["student_default_quota"] = body.student_default_quota
    log_audit(db, "admin", f"user:{admin.id}", "settings_changed", meta=changes)
    db.commit()
    return {"ok": True, "changes": changes}


# ---------- Lehrer verwalten ----------

@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db)):
    rows = db.query(User).filter_by(role="teacher").order_by(User.id).all()
    return {
        "teachers": [
            {
                "id": u.id,
                "email": u.email,
                "school": u.school,
                "disabled": u.disabled,
                "created_at": u.created_at.isoformat(),
                "projects": db.query(Project).filter_by(teacher_id=u.id).count(),
            }
            for u in rows
        ]
    }


class DisableIn(BaseModel):
    disabled: bool


@router.post("/teachers/{teacher_id}/disable")
def set_disabled(teacher_id: int, body: DisableIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(id=teacher_id, role="teacher").first()
    if not u:
        raise HTTPException(404, "Lehrer nicht gefunden")
    u.disabled = body.disabled
    for s in db.query(DbSession).filter_by(user_id=u.id).all():
        db.delete(s)
    log_audit(db, "admin", f"user:{admin.id}", "teacher_disabled" if body.disabled else "teacher_enabled", target=str(teacher_id), meta={"email": u.email})
    db.commit()
    return {"ok": True, "disabled": u.disabled}


@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    u = db.query(User).filter_by(id=teacher_id, role="teacher").first()
    if not u:
        raise HTTPException(404, "Lehrer nicht gefunden")
    for p in db.query(Project).filter_by(teacher_id=u.id).all():
        _delete_project_rows(db, p, settings)
    db.delete(u)
    log_audit(db, "admin", f"user:{admin.id}", "teacher_deleted", target=str(teacher_id), meta={"email": u.email})
    db.commit()
    return {"ok": True}


def _delete_project_rows(db: Session, p: Project, settings: Settings | None = None) -> None:
    from ..services import delete_project_cascade

    if settings is not None:
        delete_project_cascade(db, settings, p)
        return
    for a in db.query(TaskAssignment).filter_by(project_id=p.id).all():
        for sub in db.query(Submission).filter_by(assignment_id=a.id).all():
            db.query(SubmissionVersion).filter_by(submission_id=sub.id).delete()
            db.delete(sub)
        db.delete(a)
    db.query(Save).filter_by(project_id=p.id).delete()
    db.query(MediaAsset).filter_by(project_id=p.id).delete()
    db.delete(p)


@router.get("/projects")
def list_all_projects(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = db.query(Project).order_by(Project.id).all()
    return {"projects": [serialize_project(db, p, settings, with_code=True) for p in rows]}


# ---------- Audit ----------

@router.get("/audit")
def audit(limit: int = 200, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = db.query(AuditLog).filter(AuditLog.ts >= utcnow() - timedelta(days=settings.audit_retention_days)).order_by(AuditLog.id.desc()).limit(max(1, min(limit, 1000))).all()
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
