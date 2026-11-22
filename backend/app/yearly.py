from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .audit import log_audit
from .models import Project, Setting, utcnow


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.get(Setting, key)
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.flush()


def yearly_reset_point(year: int) -> datetime:
    return datetime(year, 7, 31, tzinfo=timezone.utc)


def maybe_yearly_reset(db: Session, now: datetime | None = None) -> bool:
    """Setzt am 31.07. jeden Jahres alle Projekte auf read_only (einmalig pro Jahr)."""
    now = now or utcnow()
    last = int(get_setting(db, "last_yearly_reset", "0") or 0)
    if now >= yearly_reset_point(now.year) and last < now.year:
        updated = db.query(Project).update({Project.read_only: True, Project.revision: Project.revision + 1})
        set_setting(db, "last_yearly_reset", str(now.year))
        log_audit(
            db,
            "system",
            "",
            "yearly_reset",
            target="projects",
            meta={"year": now.year, "projects_set_read_only": updated},
        )
        db.commit()
        return True
    return False
