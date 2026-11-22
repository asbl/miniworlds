from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .audit import log_audit, purge_audit
from .config import Settings
from .models import Project, aware, utcnow
from .services import delete_project_cascade
from .storage import limit_submissions
from .yearly import get_setting, set_setting


def _months_ago(now: datetime, months: int) -> datetime:
    # Näherung: 30,44 Tage/Monat
    return now - timedelta(days=months * 30.44)


def maybe_retention(db: Session, settings: Settings, now: datetime | None = None) -> dict:
    """Retention: inaktive Projekte werden nach X Monaten read-only, nach Y Monaten gelöscht."""
    now = now or utcnow()
    last = get_setting(db, "last_retention_check")
    # täglich laufen lassen
    today = now.date().isoformat()
    if last == today:
        return {"skipped": True}
    ro_limit = _months_ago(now, settings.retention_read_only_months)
    del_limit = _months_ago(now, settings.retention_delete_months)

    set_read_only = 0
    deleted = 0
    projects = db.query(Project).all()
    for p in projects:
        ref = aware(p.last_save_at) or aware(p.created_at)
        if ref < del_limit:
            pid = p.id
            delete_project_cascade(db, settings, p)
            log_audit(db, "system", "", "retention_deleted", target=f"project:{pid}", teacher_id=p.teacher_id)
            deleted += 1
        elif ref < ro_limit and not p.read_only:
            from .projects import set_read_only as mark_read_only
            mark_read_only(p, True, now)
            p.revision += 1
            log_audit(db, "system", "", "retention_read_only", target=f"project:{p.id}", teacher_id=p.teacher_id)
            set_read_only += 1
        if ref >= del_limit:
            limit_submissions(db, settings, p.id, enforce=False)
    set_setting(db, "last_retention_check", today)
    purge_audit(db, settings.audit_retention_days, now)
    db.commit()
    return {"set_read_only": set_read_only, "deleted": deleted}
