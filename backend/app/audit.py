"""Kurzes technisches Protokoll mit expliziter Lehrerzuordnung."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from .models import AuditLog, Project, User, utcnow

# Keine Titel, E-Mail-Adressen, Schulen, Remote-URLs oder Fehlermeldungen
# duplizieren. Der Meldegrund dient ausschließlich der öffentlichen Moderation.
META_KEYS = {
    "project", "projects", "snapshot", "fork", "course_id", "created", "all",
    "version", "done", "read_only", "quota_bytes", "year", "count",
    "projects_set_read_only", "declaration_version", "has_token", "public_task",
    "new_task", "teacher_quota_cap", "student_default_quota",
    "is_template_for_new_projects", "commit", "reason",
}


def audit_meta(meta: dict | None) -> dict:
    return {key: value for key, value in (meta or {}).items() if key in META_KEYS}


def log_audit(
    db: Session, actor_type: str, actor_ref: str, action: str,
    target: str = "", meta: dict | None = None, *, teacher_id: int | None = None,
) -> None:
    actor_ref = str(actor_ref)
    if actor_ref.startswith("user:"):
        actor = db.get(User, int(actor_ref.split(":", 1)[1]))
        if actor and actor.role == "teacher":
            teacher_id = actor.id
    elif actor_ref.startswith("project:"):
        project = db.get(Project, int(actor_ref.split(":", 1)[1]))
        if project:
            teacher_id = project.teacher_id
    else:
        # Insbesondere keine IP-Adressen öffentlicher Meldungen speichern.
        actor_ref = ""
    db.add(AuditLog(teacher_id=teacher_id, actor_type=actor_type, actor_ref=actor_ref,
                    action=action, target=str(target), meta=audit_meta(meta)))
    db.flush()


def purge_audit(db: Session, days: int, now=None) -> int:
    return db.query(AuditLog).filter(AuditLog.ts < (now or utcnow()) - timedelta(days=days)).delete(synchronize_session=False)
