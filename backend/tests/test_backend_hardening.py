from datetime import timedelta

import pytest

from app.audit import log_audit
from app.config import Settings, load_settings
from app.gitstore import GitError, validate_remote_url
from app.models import AuditLog, Project, Snapshot, utcnow
from app.retention import maybe_retention
from app.yearly import get_setting

from .conftest import create_project, make_teacher
from .test_share import _setup


def test_project_deletion_removes_public_media(client, teacher_csrf, app, settings):
    from pathlib import Path
    from .conftest import auth
    p, token = _setup(client, teacher_csrf)
    rid = client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token)).json()["id"]
    approved = client.post(f"/api/teacher/share-requests/{rid}/approve", json={"slug": "delete-all"}, headers={"X-CSRF-Token": teacher_csrf})
    assert approved.status_code == 200, approved.text
    sid = approved.json()["snapshot_id"]
    folder = Path(settings.media_root) / "snapshots" / str(sid)
    assert list(folder.iterdir())
    assert client.delete(f"/api/teacher/projects/{p['id']}", headers={"X-CSRF-Token": teacher_csrf}).status_code == 200
    assert not folder.exists()
    with app.state.SessionLocal() as db:
        assert db.get(Snapshot, sid) is None
    assert client.get("/api/public/delete-all").status_code == 404


def test_audit_is_scoped_and_has_no_duplicate_personal_fields(client, client2, teacher_csrf, app):
    p = create_project(client, teacher_csrf)[0]
    with app.state.SessionLocal() as db:
        teacher_id = db.get(Project, p["id"]).teacher_id
        log_audit(db, "system", "", "retention_read_only", target=f"project:{p['id']}", teacher_id=teacher_id)
        log_audit(db, "teacher", f"user:{teacher_id}", "project_updated", meta={"email": "private@example.org", "title": "Private Name", "done": True})
        log_audit(db, "anonymous", "192.0.2.42", "public_report", target="snapshot:1")
        db.commit()
    own = client.get("/api/teacher/audit").json()["entries"]
    assert any(e["action"] == "retention_read_only" for e in own)
    assert "private@example.org" not in str(own) and "Private Name" not in str(own)
    assert "lehrer@schule.de" not in str(own)
    make_teacher(client2, email="other@schule.de")
    other = client2.get("/api/teacher/audit").json()["entries"]
    assert not any(e["action"] == "retention_read_only" for e in other)
    with app.state.SessionLocal() as db:
        assert db.query(AuditLog).filter_by(action="public_report").one().actor_ref == ""


def test_retention_persists_empty_run_and_expires_logs(client, teacher_csrf, app, settings):
    create_project(client, teacher_csrf)
    now = utcnow()
    with app.state.SessionLocal() as db:
        db.add(AuditLog(actor_type="system", actor_ref="", action="expired", ts=now-timedelta(days=31)))
        db.commit()
        assert maybe_retention(db, settings, now) == {"set_read_only": 0, "deleted": 0}
    with app.state.SessionLocal() as db:
        assert get_setting(db, "last_retention_check") == now.date().isoformat()
        assert maybe_retention(db, settings, now) == {"skipped": True}
        assert db.query(AuditLog).filter_by(action="expired").count() == 0


def test_missing_secret_is_rejected_before_startup(monkeypatch):
    from app.main import create_app
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        load_settings()
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(Settings())


def test_changed_secret_is_rejected_and_original_key_still_works(client, teacher_csrf, settings):
    from dataclasses import replace
    from app.main import create_app
    from fastapi.testclient import TestClient
    from .conftest import student_token, auth
    project = create_project(client, teacher_csrf)[0]
    with pytest.raises(ValueError, match="SECRET_KEY passt nicht"):
        create_app(replace(settings, secret_key="accidentally-changed"), enable_yearly_task=False)
    restarted = create_app(settings, enable_yearly_task=False)
    with TestClient(restarted) as other:
        token = student_token(other, project["code"])
        assert other.get("/api/play/project", headers=auth(token)).status_code == 200
    restarted.state.engine.dispose()


def test_maintenance_does_not_block_http_or_repeat_per_request(settings, monkeypatch):
    import threading
    import app.main as main
    from fastapi.testclient import TestClient
    started, release = threading.Event(), threading.Event()
    calls = []
    def slow_maintenance(*args):
        calls.append(True)
        started.set()
        release.wait(5)
    monkeypatch.setattr(main, "run_maintenance", slow_maintenance)
    application = main.create_app(settings, enable_yearly_task=True)
    try:
        with TestClient(application) as http:
            assert started.wait(2)
            try:
                for _ in range(3):
                    assert http.get("/healthz").status_code == 200
                assert len(calls) == 1
            finally:
                release.set()
    finally:
        release.set()
        application.state.engine.dispose()


def test_backup_lock_blocks_writes_but_allows_reads(client, teacher_csrf, settings):
    import threading
    from app.locking import storage_lock
    complete = threading.Event()
    result = []
    def write():
        try:
            result.append(client.post("/api/teacher/projects", json={"count": 1}, headers={"X-CSRF-Token": teacher_csrf}).status_code)
        finally:
            complete.set()
    with storage_lock(settings, exclusive=True):
        worker = threading.Thread(target=write)
        worker.start()
        assert not complete.wait(0.15)
        assert client.get("/healthz").status_code == 200
    worker.join(3)
    assert not worker.is_alive() and result == [200]


def test_legacy_audit_is_pseudonymized_and_scoped(client, teacher_csrf, app):
    from sqlalchemy import text
    from app.migrations import migrate
    project = create_project(client, teacher_csrf)[0]
    with app.state.engine.begin() as connection:
        connection.execute(text("DELETE FROM settings WHERE key='technical_audit_v1'"))
        connection.execute(text("INSERT INTO audit_log (ts,actor_type,actor_ref,action,target,meta) VALUES (:now,'teacher','lehrer@schule.de','legacy','project:1',:meta)"),
                           {"now": utcnow(), "meta": '{"email":"private@example.test","title":"private","done":true}'})
        connection.execute(text("INSERT INTO audit_log (ts,actor_type,actor_ref,action,target,meta) VALUES (:now,'system','','legacy_system',:target,'{}')"),
                           {"now": utcnow(), "target": f"project:{project['id']}"})
    migrate(app.state.engine)
    entries = client.get("/api/teacher/audit").json()["entries"]
    legacy = next(e for e in entries if e["action"] == "legacy")
    assert legacy["actor_ref"].startswith("user:") and legacy["meta"] == {"done": True}
    assert any(e["action"] == "legacy_system" for e in entries)
    assert "lehrer@schule.de" not in str(entries) and "private@example.test" not in str(entries)


def test_git_blocks_private_dns_and_normalizes_hosts(monkeypatch):
    from app import gitstore
    def addresses(*args, **kwargs):
        return [(2, 1, 6, "", ("127.0.0.1", 443))]
    monkeypatch.setattr(gitstore.socket, "getaddrinfo", addresses)
    for url, allowed in [
        ("git@LOCALHOST:repo.git", "localhost"),
        ("https://git.example.org/repo.git", "git.example.org"),
        ("git@git.example.org:repo.git", "git.example.org"),
        ("https://127.0.0.1/repo.git", "127.0.0.1"),
        ("https://[::1]/repo.git", "::1"),
    ]:
        with pytest.raises(GitError, match="Interne/lokale"):
            validate_remote_url(url, allowed)
    monkeypatch.setattr(gitstore.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert validate_remote_url("git@GITHUB.COM:u/r.git") == "git@github.com:u/r.git"
    with pytest.raises(GitError):
        validate_remote_url("https://evil.github.com/u/r.git")
    with pytest.raises(GitError):
        validate_remote_url("https://github.com/u/r.git", "")
    # Der Test-Schalter erlaubt lokale Dateien, aber keine internen Netzwerkziele.
    with pytest.raises(GitError):
        validate_remote_url("git@LOCALHOST:r.git", "local")
