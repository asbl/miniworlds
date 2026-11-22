from __future__ import annotations

import base64
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.main import create_app
from app.migrations import migrate
from app.models import AuditLog, Project, SubmissionVersion

from .conftest import auth, create_project, make_teacher, student_token
from .test_tasks import _add_item, _mk_task

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def course(client, csrf, title="Informatik 7a"):
    r = client.post("/api/teacher/courses", json={"title": title, "school_year": "2026/27"}, headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_class_login_accepts_30_valid_codes_but_limits_failures(client, teacher_csrf):
    projects = create_project(client, teacher_csrf, count=30)
    assert all(client.post("/api/claim", json={"code": p["code"]}).status_code == 200 for p in projects)
    assert all(client.post("/api/claim", json={"code": f"wrong-{n}"}).status_code == 401 for n in range(20))
    assert client.post("/api/claim", json={"code": "another-wrong-code"}).status_code == 429


def test_two_tabs_cannot_overwrite_each_other(client, teacher_csrf):
    token = student_token(client, create_project(client, teacher_csrf)[0]["code"])
    h = auth(token)
    revision = client.get("/api/play/project", headers=h).json()["revision"]
    first = client.put("/api/play/save", json={"source": "newer", "base_revision": revision}, headers=h)
    assert first.status_code == 200
    assert first.json()["revision"] == revision + 1
    stale = client.put("/api/play/save", json={"source": "older", "base_revision": revision}, headers=h)
    assert stale.status_code == 409
    assert client.get("/api/play/project", headers=h).json()["save"]["source"] == "newer"
    # Omitting a revision cannot bypass the conflict check, either.
    assert client.put("/api/play/save", json={"source": "no version"}, headers=h).status_code == 409


def test_simultaneous_saves_have_one_winner(app, client, teacher_csrf, monkeypatch):
    from app import gitstore
    monkeypatch.setattr(gitstore, "git_available", lambda: False)
    token = student_token(client, create_project(client, teacher_csrf)[0]["code"])
    def save(source):
        with TestClient(app) as tab:
            return tab.put("/api/play/save", json={"source": source, "base_revision": 0}, headers=auth(token))
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(save, ["one", "two"]))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert client.get("/api/play/project", headers=auth(token)).json()["revision"] == 1


def test_workspace_projects_are_isolated_and_code_login_survives(client, teacher_csrf):
    first, outsider = create_project(client, teacher_csrf, count=2)
    h = auth(student_token(client, first["code"]))
    second = client.post("/api/play/projects", json={"title": "Spiel zwei"}, headers=h)
    assert second.status_code == 200
    second = second.json()
    choices = client.get("/api/play/projects", headers=h).json()["projects"]
    assert {p["id"] for p in choices} == {first["id"], second["project_id"]}
    assert client.post(f'/api/play/projects/{outsider["id"]}/open', headers=h).status_code == 404
    opened = client.post(f'/api/play/projects/{second["project_id"]}/open', headers=h)
    assert opened.status_code == 200
    assert client.get("/api/play/project", headers=auth(opened.json()["token"])).json()["title"] == "Spiel zwei"
    assert client.post("/api/claim", json={"code": first["code"]}).status_code == 200


def test_class_archive_is_reversible_and_keeps_manual_locks(client, teacher_csrf):
    th = {"X-CSRF-Token": teacher_csrf}
    cid = course(client, teacher_csrf)
    p = client.post("/api/teacher/projects", json={"count": 1, "course_id": cid}, headers=th).json()["projects"][0]
    h = auth(student_token(client, p["code"]))
    assert client.patch(f'/api/teacher/projects/{p["id"]}', json={"read_only": True}, headers=th).status_code == 200
    assert client.patch(f"/api/teacher/courses/{cid}", json={"archived": True}, headers=th).status_code == 200
    assert client.get("/api/play/project", headers=h).json()["read_only"] is True
    assert client.put("/api/play/save", json={"source": "x"}, headers=h).status_code == 403
    assert client.post("/api/play/projects", json={"title": "x"}, headers=h).status_code == 403
    assert client.post("/api/play/media", files={"file": ("a.png", PNG, "image/png")}, headers=h).status_code == 403
    assert client.get("/api/play/download", headers=h).status_code == 200
    assert client.post("/api/teacher/projects", json={"course_id": cid}, headers=th).status_code == 409
    assert client.patch(f"/api/teacher/courses/{cid}", json={"archived": False}, headers=th).status_code == 200
    assert client.get("/api/play/project", headers=h).json()["read_only"] is True
    client.patch(f'/api/teacher/projects/{p["id"]}', json={"read_only": False}, headers=th)
    revision = client.get("/api/play/project", headers=h).json()["revision"]
    assert client.put("/api/play/save", json={"source": "back", "base_revision": revision}, headers=h).status_code == 200


def test_course_templates_only_apply_in_their_class(client, teacher_csrf):
    th = {"X-CSRF-Token": teacher_csrf}
    cid = course(client, teacher_csrf)
    task = client.post("/api/teacher/tasks", json={"title": "7a Aufgabe", "course_id": cid, "is_template_for_new_projects": True}, headers=th).json()["task"]
    inside = client.post("/api/teacher/projects", json={"course_id": cid}, headers=th).json()["projects"][0]
    outside = create_project(client, teacher_csrf)[0]
    assert len(client.get("/api/play/project", headers=auth(student_token(client, inside["code"]))).json()["tasks"]) == 1
    assert client.get("/api/play/project", headers=auth(student_token(client, outside["code"]))).json()["tasks"] == []
    result = client.post(f'/api/teacher/tasks/{task["id"]}/assign', json={"all": True}, headers=th)
    assert result.json()["created"] == 0


def test_bulk_changes_and_courses_respect_teacher_ownership(client, client2, teacher_csrf):
    own = create_project(client, teacher_csrf)[0]
    cid = course(client, teacher_csrf)
    other_csrf = make_teacher(client2, email="another@schule.de")
    other = create_project(client2, other_csrf)[0]
    th = {"X-CSRF-Token": teacher_csrf}
    assert client.patch("/api/teacher/projects/bulk", json={"project_ids": [own["id"], other["id"]], "read_only": True}, headers=th).status_code == 404
    assert client.get(f'/api/teacher/projects/{own["id"]}').json()["read_only"] is False
    assert client2.patch(f"/api/teacher/courses/{cid}", json={"archived": True}, headers={"X-CSRF-Token": other_csrf}).status_code == 404
    assert client2.post("/api/teacher/projects", json={"course_id": cid}, headers={"X-CSRF-Token": other_csrf}).status_code == 404
    result = client.patch("/api/teacher/projects/bulk", json={"project_ids": [own["id"]], "course_id": cid, "read_only": True}, headers=th)
    assert result.status_code == 200
    assert client.get(f'/api/teacher/projects/{own["id"]}').json()["course_id"] == cid


def test_submission_keeps_code_database_media_and_task_after_edits(client, teacher_csrf):
    th = {"X-CSRF-Token": teacher_csrf}
    p = create_project(client, teacher_csrf)[0]
    h = auth(student_token(client, p["code"]))
    tid = _mk_task(client, teacher_csrf)
    item = _add_item(client, teacher_csrf, tid, "checkbox", "Originalfrage")
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers=th)
    aid = client.get("/api/play/project", headers=h).json()["tasks"][0]["assignment_id"]
    dbdata = base64.b64encode(b"sqlite-data").decode()
    assert client.put("/api/play/save", json={"source": "print('original')", "db": dbdata}, headers=h).status_code == 200
    upload = client.post("/api/play/media", files={"file": ("bild.png", PNG, "image/png")}, data={"license": "CC0", "source": "self"}, headers=h).json()["media"]
    assert client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(item): {"checked": True}}}, headers=h).status_code == 200
    submitted = client.post(f"/api/play/tasks/{aid}/submit?base_revision=1", headers=h)
    assert submitted.status_code == 200
    row = client.get(f"/api/teacher/tasks/{tid}/submissions").json()["submissions"][0]
    sid, version = row["submission_id"], submitted.json()["version"]
    assert client.put("/api/play/save", json={"source": "print('changed')", "base_revision": 1}, headers=h).status_code == 200
    assert client.delete(f'/api/play/media/{upload["id"]}', headers=h).status_code == 200
    client.patch(f"/api/teacher/tasks/{tid}/items/{item}", json={"prompt": "Geänderte Frage"}, headers=th)
    result = client.get(f"/api/teacher/submissions/{sid}/versions/{version}").json()
    frozen = result["snapshot"]
    assert frozen["save"] == {"source": "print('original')", "db": dbdata}
    assert frozen["task"]["items"][0]["prompt"] == "Originalfrage"
    assert base64.b64decode(frozen["media"][0]["content"]) == PNG
    assert result["answers"][str(item)]["checked"] is True
    zipped = client.get(f"/api/teacher/submissions/{sid}/versions/{version}/download")
    with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
        assert archive.read("main.py") == b"print('original')"
        assert archive.read("bild.png") == PNG
        assert archive.read("save.db") == b"sqlite-data"
    # No teacher/student comment fields in persistence or API.
    assert "teacher_note" not in row and "feedback" not in row
    assert client.patch(f"/api/teacher/submissions/{sid}", json={"teacher_note": "must not be saved"}, headers=th).status_code == 422
    assert client.patch(f"/api/teacher/submissions/{sid}", json={"feedback": "must not be saved"}, headers=th).status_code == 422


def test_zip_download_is_portable_and_authenticated(client, client2, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    h = auth(student_token(client, p["code"]))
    client.put("/api/play/save", json={"source": "print('portable')"}, headers=h)
    client.post("/api/play/media", files={"file": ("../test image.png", PNG, "image/png")}, data={"license": "CC0", "source": "test"}, headers=h)
    assert client2.get("/api/play/download").status_code == 401
    r = client.get("/api/play/download", headers=h)
    assert r.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
        assert archive.read("main.py") == b"print('portable')"
        assert archive.read("test_image.png") == PNG
        assert json.loads(archive.read("licenses.json"))[0]["license"] == "CC0"
        assert all(".." not in name for name in archive.namelist())


def test_snapshot_ownership_and_opaque_runner_boundary(client, client2, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    other_csrf = make_teacher(client2, email="outsider@schule.de")
    assert client2.get(f'/api/teacher/projects/{p["id"]}/snapshot').status_code == 404
    page = client.get("/play")
    assert "workspace.js" in page.text and "player.js" not in page.text
    runner = client.get("/runner")
    csp = runner.headers["content-security-policy"]
    assert "sandbox allow-scripts;" in csp and "allow-same-origin" not in csp
    assert "connect-src https://cdn.jsdelivr.net/pyodide/" in csp
    assert "connect-src 'self'" not in csp
    assert "frame-ancestors 'self'" in csp
    assert "unsafe-eval" not in page.headers["content-security-policy"].replace("wasm-unsafe-eval", "")


def test_migration_removes_old_notes_and_preserves_projects(app, settings):
    with app.state.engine.begin() as conn:
        conn.execute(text("ALTER TABLE submissions ADD COLUMN teacher_note TEXT"))
        conn.execute(text("ALTER TABLE submissions ADD COLUMN feedback TEXT"))
        conn.execute(text("INSERT INTO audit_log (ts,actor_type,actor_ref,action,target,meta) VALUES ('2026-01-01','teacher','test','submission_reviewed','submission:1',:meta)"), {"meta": json.dumps({"teacher_note": "old private note", "feedback": "old feedback", "done": True})})
    migrate(app.state.engine)
    migrate(app.state.engine)
    columns = {c["name"] for c in inspect(app.state.engine).get_columns("submissions")}
    assert "teacher_note" not in columns and "feedback" not in columns
    with app.state.SessionLocal() as db:
        assert db.query(AuditLog).one().meta == {"done": True}
    # Reopening the same database is safe and idempotent.
    reopened = create_app(settings, enable_yearly_task=False)
    reopened.state.engine.dispose()


def test_answers_conflicts_do_not_store_unrelated_fields(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    tid = _mk_task(client, teacher_csrf)
    iid = _add_item(client, teacher_csrf, tid, "checkbox", "Getestet")
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers={"X-CSRF-Token": teacher_csrf})
    h = auth(student_token(client, p["code"]))
    aid = client.get("/api/play/project", headers=h).json()["tasks"][0]["assignment_id"]
    url = f"/api/play/tasks/{aid}/answers"
    assert client.put(url, json={"answers": {"feedback": {"text": "irrelevant"}}}, headers=h).status_code == 422
    assert client.put(url, json={"answers": {str(iid): {"checked": True}}, "base_version": 0}, headers=h).status_code == 200
    assert client.put(url, json={"answers": {str(iid): {"checked": False}}, "base_version": 0}, headers=h).status_code == 409
    assert client.put(url, json={"answers": {str(iid): {"checked": False}}, "base_version": 1}, headers=h).status_code == 200
    with client.app.state.SessionLocal() as db:
        assert db.query(SubmissionVersion).count() == 1


def test_code_rotation_revokes_every_project_token_in_workspace(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    old = student_token(client, p["code"])
    sibling = client.post("/api/play/projects", json={"title": "Zweites Projekt"}, headers=auth(old)).json()
    response = client.post(f'/api/teacher/projects/{p["id"]}/regenerate-code', json={}, headers={"X-CSRF-Token": teacher_csrf})
    assert response.status_code == 200
    assert client.get("/api/play/project", headers=auth(old)).status_code == 401
    assert client.get("/api/play/project", headers=auth(sibling["token"])).status_code == 401
    current = student_token(client, response.json()["code"])
    assert client.post(f'/api/play/projects/{sibling["project_id"]}/open', headers=auth(current)).status_code == 200


def test_legacy_schema_migration_keeps_code_and_save(settings, tmp_path):
    import sqlite3
    from dataclasses import replace
    from app.security import encrypt_code, hash_code

    path = tmp_path / "legacy.db"
    legacy = replace(settings, database_url=f"sqlite:///{path}")
    code = "LEGACY23456"
    payload = json.dumps({"source": "keep this", "db": None}).encode()
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, role VARCHAR(16), email VARCHAR(255),
                pw_hash VARCHAR(255), school VARCHAR(255), disabled BOOLEAN, created_at DATETIME);
            CREATE TABLE projects (id INTEGER PRIMARY KEY, code_hash VARCHAR(64) UNIQUE,
                code_enc VARCHAR(512), teacher_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                quota_bytes INTEGER, read_only BOOLEAN, created_at DATETIME, last_save_at DATETIME);
            CREATE TABLE saves (project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                payload BLOB, size_bytes INTEGER, updated_at DATETIME);
            CREATE TABLE tasks (id INTEGER PRIMARY KEY, teacher_id INTEGER REFERENCES users(id),
                title VARCHAR(255), description TEXT, is_template_for_new_projects BOOLEAN,
                created_at DATETIME, updated_at DATETIME);
            CREATE TABLE submission_versions (id INTEGER PRIMARY KEY,
                submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
                version INTEGER, payload BLOB, submitted BOOLEAN, created_at DATETIME);
        """)
        conn.execute("INSERT INTO users VALUES (1,'teacher','legacy@example.test','unused','Testschule',0,'2026-01-01')")
        conn.execute("INSERT INTO projects VALUES (1,?,?,1,10485760,0,'2026-01-01','2026-01-01')", (hash_code(code), encrypt_code(code, settings.secret_key)))
        conn.execute("INSERT INTO saves VALUES (1,?,?,'2026-01-01')", (payload, len(payload)))
    migrated = create_app(legacy, enable_yearly_task=False)
    try:
        with TestClient(migrated) as c:
            token = student_token(c, code)
            project = c.get("/api/play/project", headers=auth(token)).json()
            assert project["save"]["source"] == "keep this"
            assert project["workspace_id"] is not None
            assert project["revision"] == 0
            assert c.put("/api/play/save", json={"source": "after migration", "base_revision": 0}, headers=auth(token)).status_code == 200
    finally:
        migrated.state.engine.dispose()
