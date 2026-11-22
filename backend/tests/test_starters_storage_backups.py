import io
import json
import secrets
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import gitstore
from app.backups import create_backup, restore_backup, verify_backup
from app.config import Settings
from app.main import create_app
from app.models import ProjectRemote, SubmissionVersion

from .conftest import auth, create_project, student_token
from .test_share import _setup


def _task(client, csrf, pid, course_id=None):
    headers = {"X-CSRF-Token": csrf}
    response = client.post("/api/teacher/tasks", json={"title": "Startaufgabe", "course_id": course_id}, headers=headers)
    assert response.status_code == 200, response.text
    tid = response.json()["task"]["id"]
    response = client.post(f"/api/teacher/tasks/{tid}/items", json={"kind": "checkbox", "prompt": "Programm getestet"}, headers=headers)
    assert response.status_code == 200, response.text
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [pid]}, headers=headers)
    return tid


def _save(client, token, source):
    revision = client.get("/api/play/project", headers=auth(token)).json()["revision"]
    response = client.put("/api/play/save", json={"source": source, "base_revision": revision}, headers=auth(token))
    assert response.status_code == 200, response.text
    return response.json()


def test_class_starter_copies_content_and_tasks_without_previous_work(client, client2, teacher_csrf, app):
    headers = {"X-CSRF-Token": teacher_csrf}
    source, token = _setup(client, teacher_csrf)
    old_course = client.post("/api/teacher/courses", json={"title": "Vorlagen"}, headers=headers).json()["id"]
    new_course = client.post("/api/teacher/courses", json={"title": "Neue Klasse"}, headers=headers).json()["id"]
    _task(client, teacher_csrf, source["id"], old_course)
    task = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]
    aid, item = task["assignment_id"], str(task["items"][0]["id"])
    assert client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {item: {"checked": True}}}, headers=auth(token)).status_code == 200
    assert client.post(f"/api/play/tasks/{aid}/submit", headers=auth(token)).status_code == 200
    client.put("/api/play/remote", json={"url": "/test/remote.git", "token": "must-not-copy"}, headers=auth(token))
    response = client.post("/api/teacher/projects", json={"count": 2, "course_id": new_course, "template_project_id": source["id"]}, headers=headers)
    assert response.status_code == 200, response.text
    copies = response.json()["projects"]
    for copy in copies:
        copied_token = student_token(client2, copy["code"])
        data = client2.get("/api/play/project", headers=auth(copied_token)).json()
        assert data["course_id"] == new_course
        assert data["save"]["source"] == "print('v1')"
        assert len(data["media"]) == 1 and data["media"][0]["license"] == "CC0"
        assert data["tasks"][0]["answers"] == {} and data["tasks"][0]["status"] == "open"
        copied_task = client.get(f"/api/teacher/tasks/{data['tasks'][0]['task_id']}").json()["task"]
        assert copied_task["course_id"] == new_course
        with app.state.SessionLocal() as db:
            assert db.get(ProjectRemote, copy["id"]) is None
        assert client2.get(f"/api/play/media/{data['media'][0]['id']}/file", headers=auth(copied_token)).status_code == 200
    # Kopien sind eigenständig und bleiben nach dem Löschen der Vorlage erhalten.
    client.delete(f"/api/teacher/projects/{source['id']}", headers=headers)
    assert client2.get(f"/api/play/media/{data['media'][0]['id']}/file", headers=auth(copied_token)).status_code == 200
    assert client2.get("/api/play/project", headers=auth(copied_token)).json()["save"]["source"] == "print('v1')"


def test_starter_rejects_other_teacher_and_oversize(client, client2, teacher_csrf, settings):
    from .conftest import make_teacher
    source, token = _setup(client, teacher_csrf)
    other_csrf = make_teacher(client2, email="other-starter@schule.de")
    assert client2.post("/api/teacher/projects", json={"template_project_id": source["id"]}, headers={"X-CSRF-Token": other_csrf}).status_code == 404
    from app.yearly import set_setting
    with client.app.state.SessionLocal() as db:
        set_setting(db, "student_default_quota", "1")
        db.commit()
    before = len(client.get("/api/teacher/projects").json()["projects"])
    response = client.post("/api/teacher/projects", json={"count": 2, "template_project_id": source["id"]}, headers={"X-CSRF-Token": teacher_csrf})
    assert response.status_code == 413
    assert len(client.get("/api/teacher/projects").json()["projects"]) == before


def test_submission_history_is_bounded_and_keeps_latest(client, teacher_csrf, app, settings):
    settings.submission_max_versions = 2
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _task(client, teacher_csrf, p["id"])
    for index in range(5):
        _save(client, token, f"step = {index}\n")
        task = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]
        aid = task["assignment_id"]
        response = client.post(f"/api/play/tasks/{aid}/submit", headers=auth(token))
        assert response.status_code == 200, response.text
        sid = client.get(f"/api/teacher/tasks/{task['task_id']}/submissions").json()["submissions"][0]["submission_id"]
        if index != 4:
            assert client.post(f"/api/teacher/submissions/{sid}/reopen", headers={"X-CSRF-Token": teacher_csrf}).status_code == 200
    versions = client.get(f"/api/teacher/submissions/{sid}/versions").json()["versions"]
    assert len(versions) == 2
    latest = max(v["version"] for v in versions)
    assert client.get(f"/api/teacher/submissions/{sid}/versions/{latest}").json()["snapshot"]["save"]["source"] == "step = 4\n"


def test_oversize_submission_is_rejected_without_changing_existing_state(client, teacher_csrf, app, settings):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _task(client, teacher_csrf, p["id"])
    task = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]
    settings.submission_max_bytes = 1
    assert client.post(f"/api/play/tasks/{task['assignment_id']}/submit", headers=auth(token)).status_code == 413
    current = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]
    assert current["status"] == "open" and current["version"] == 0
    with app.state.SessionLocal() as db:
        assert db.query(SubmissionVersion).count() == 0


def test_history_budget_preserves_current_save_and_supports_export_and_clear(client, teacher_csrf, settings, tmp_path):
    settings.history_max_bytes = 100_000
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _save(client, token, "before = 1\n")
    large_source = secrets.token_hex(200_000)
    saved = _save(client, token, large_source)
    assert saved["warning"] and "gespeichert" in saved["warning"]
    assert client.get("/api/play/project", headers=auth(token)).json()["save"]["source"] == large_source
    history = client.get("/api/play/history", headers=auth(token)).json()
    assert history["paused"] and history["used_bytes"] <= settings.history_max_bytes
    assert len(history["commits"]) == 1
    assert json.loads(gitstore.read_save_at(settings, p["id"], "HEAD"))["source"] == "before = 1\n"
    bundle = client.get("/api/play/history/download", headers=auth(token))
    assert bundle.status_code == 200 and bundle.content.startswith(b"# v2 git bundle")
    response = client.delete(f"/api/play/history?base_revision={saved['revision']}", headers=auth(token))
    assert response.status_code == 200, response.text
    assert client.get("/api/play/project", headers=auth(token)).json()["save"]["source"] == large_source
    _save(client, token, "after = 2\n")
    assert not client.get("/api/play/history", headers=auth(token)).json()["paused"]


def test_backup_restores_database_public_media_and_git(client, teacher_csrf, settings, tmp_path):
    source, token = _setup(client, teacher_csrf)
    _task(client, teacher_csrf, source["id"])
    task = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]
    assert client.post(f"/api/play/tasks/{task['assignment_id']}/submit", headers=auth(token)).status_code == 200
    rid = client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token)).json()["id"]
    assert client.post(f"/api/teacher/share-requests/{rid}/approve", json={"slug": "backup-public"}, headers={"X-CSRF-Token": teacher_csrf}).status_code == 200
    backups = tmp_path / "backups"
    archive = create_backup(settings, backups, keep=2)
    assert verify_backup(archive, settings.secret_key)["projects"] == 1
    restored = tmp_path / "restored"
    restore_backup(archive, restored, settings.secret_key)
    restored_settings = Settings(**{**settings.__dict__, "database_url": f"sqlite:///{restored}/app.db", "media_root": str(restored / "media"), "git_root": str(restored / "git")})
    restored_app = create_app(restored_settings, enable_yearly_task=False)
    with TestClient(restored_app) as restored_client:
        restored_token = student_token(restored_client, source["code"])
        data = restored_client.get("/api/play/project", headers=auth(restored_token)).json()
        assert data["save"]["source"] == "print('v1')" and data["tasks"][0]["status"] == "submitted"
        assert restored_client.get("/api/public/backup-public").status_code == 200
        mid = data["media"][0]["id"]
        assert restored_client.get(f"/api/play/media/{mid}/file", headers=auth(restored_token)).status_code == 200
        assert restored_client.get("/api/play/history", headers=auth(restored_token)).json()["commits"]
    restored_app.state.engine.dispose()
    with pytest.raises(ValueError, match="Signatur"):
        verify_backup(archive, "wrong-secret")
    with pytest.raises(ValueError, match="nicht überschrieben"):
        restore_backup(archive, restored, settings.secret_key)
    damaged = tmp_path / "damaged.zip"
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(damaged, "w") as broken:
        for name in original.namelist():
            content = original.read(name)
            if name == f"media/{source['id']}/1.png":
                content = content[:-1] + b"!"
            broken.writestr(name, content)
    with pytest.raises(ValueError, match="Prüfsumme"):
        verify_backup(damaged, settings.secret_key)
    create_backup(settings, backups, keep=2)
    create_backup(settings, backups, keep=2)
    assert len(list(backups.glob("*.zip"))) == 2
