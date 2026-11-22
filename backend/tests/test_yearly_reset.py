from __future__ import annotations

from datetime import datetime, timezone

from app.yearly import maybe_yearly_reset

from .conftest import create_project


def _db(app):
    return app.state.SessionLocal()


def test_reset_after_july31_sets_read_only(app, client, teacher_csrf):
    create_project(client, teacher_csrf, count=2)
    db = _db(app)
    try:
        # Vor dem 31.07. passiert nichts
        assert maybe_yearly_reset(db, now=datetime(2026, 7, 30, 23, 59, tzinfo=timezone.utc)) is False
        # Nach dem 31.07. werden alle Projekte read-only
        assert maybe_yearly_reset(db, now=datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)) is True
        from app.models import Project

        assert all(p.read_only for p in db.query(Project).all())
        # Idempotent: erneuter Aufruf im selben Jahr macht nichts
        assert maybe_yearly_reset(db, now=datetime(2026, 9, 1, tzinfo=timezone.utc)) is False
        # Audit-Eintrag vorhanden
        from app.models import AuditLog

        actions = [a.action for a in db.query(AuditLog).all()]
        assert "yearly_reset" in actions
        # Nächstes Jahr greift es erneut
        assert maybe_yearly_reset(db, now=datetime(2027, 8, 1, tzinfo=timezone.utc)) is True
    finally:
        db.close()


def test_no_reset_before_first_of_august_on_fresh_db(app, client, teacher_csrf):
    create_project(client, teacher_csrf, count=1)
    db = _db(app)
    try:
        from app.models import Project

        assert maybe_yearly_reset(db, now=datetime(2026, 7, 31, 0, 0, tzinfo=timezone.utc)) is True  # exakt am 31.07. 00:00
        db.query(Project).update({"read_only": False})
        db.commit()
        assert maybe_yearly_reset(db, now=datetime(2026, 7, 30, tzinfo=timezone.utc)) is False
    finally:
        db.close()
