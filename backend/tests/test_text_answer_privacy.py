from __future__ import annotations

import io
import json
import zipfile
import zlib

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.models import PublicTask, SubmissionVersion, TaskItem

from .conftest import auth, create_project, student_token
from .test_tasks import _add_item, _mk_task


def test_text_answers_are_rejected_and_never_saved(client, teacher_csrf, app):
    th = {"X-CSRF-Token": teacher_csrf}
    p = create_project(client, teacher_csrf)[0]
    tid = _mk_task(client, teacher_csrf)
    iid = _add_item(client, teacher_csrf, tid, "checkbox", "Programm getestet")
    assert client.post(f"/api/teacher/tasks/{tid}/items", json={"kind": "textarea", "prompt": "Antwort"}, headers=th).status_code == 400
    assert client.patch(f"/api/teacher/tasks/{tid}/items/{iid}", json={"kind": "textarea"}, headers=th).status_code == 400
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers=th)
    h = auth(student_token(client, p["code"]))
    aid = client.get("/api/play/project", headers=h).json()["tasks"][0]["assignment_id"]
    for answer in ({"text": "private answer"}, {"checked": True, "text": "private answer"}, "private answer", {"checked": "private answer"}):
        r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(iid): answer}}, headers=h)
        assert r.status_code == 422, r.text
    with app.state.SessionLocal() as db:
        assert db.query(SubmissionVersion).count() == 0
    accepted = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(iid): {"checked": True}}}, headers=h)
    assert accepted.status_code == 200
    assert client.get("/api/play/project", headers=h).json()["tasks"][0]["answers"] == {str(iid): {"checked": True}}


def test_migration_removes_historical_text_answers_and_preserves_programs(client, teacher_csrf, app, settings):
    th = {"X-CSRF-Token": teacher_csrf}
    p = create_project(client, teacher_csrf)[0]
    h = auth(student_token(client, p["code"]))
    tid = _mk_task(client, teacher_csrf)
    checkbox = _add_item(client, teacher_csrf, tid, "checkbox", "Programm getestet")
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers=th)
    aid = client.get("/api/play/project", headers=h).json()["tasks"][0]["assignment_id"]
    assert client.put("/api/play/save", json={"source": "print('CODE_STAYS')"}, headers=h).status_code == 200
    client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(checkbox): {"checked": True}}}, headers=h)
    client.post(f"/api/play/tasks/{aid}/submit?base_revision=1", headers=h)
    sid = client.get(f"/api/teacher/tasks/{tid}/submissions").json()["submissions"][0]["submission_id"]
    public_id = client.post(f"/api/teacher/tasks/{tid}/publish", json={}, headers=th).json()["public_task"]["id"]
    secret = "LEGACY_PRIVATE_TEXT_TO_REMOVE"
    with app.state.SessionLocal() as db:
        old_item = TaskItem(task_id=tid, kind="textarea", prompt="Frühere Frage", position=1)
        db.add(old_item)
        db.flush()
        answers = {str(checkbox): {"checked": True, "text": secret}, str(old_item.id): {"text": secret}, "unknown": {"text": secret}}
        versions = db.query(SubmissionVersion).order_by(SubmissionVersion.version).all()
        for version in versions:
            version.payload = json.dumps(answers).encode()
            if version.project_snapshot:
                snapshot = json.loads(zlib.decompress(version.project_snapshot))
                snapshot["task"]["items"].append({"id": old_item.id, "kind": "textarea", "prompt": "Frühere Frage", "position": 1})
                snapshot["answers"] = answers
                version.project_snapshot = zlib.compress(json.dumps(snapshot).encode())
        public = db.get(PublicTask, public_id)
        public.items = json.dumps([{"kind": "textarea", "prompt": "Frühere Frage", "position": 0}]).encode()
        # Simulate an existing installation that has not run this privacy migration.
        db.execute(text("DELETE FROM settings WHERE key='checkbox_only_v1'"))
        db.commit()
    migrated = create_app(settings, enable_yearly_task=False)
    try:
        with migrated.state.SessionLocal() as db:
            assert {item.kind for item in db.query(TaskItem)} == {"text", "checkbox"}
            for version in db.query(SubmissionVersion):
                assert json.loads(version.payload) == {str(checkbox): {"checked": True}}
                if version.project_snapshot:
                    raw = json.loads(zlib.decompress(version.project_snapshot))
                    assert secret not in json.dumps(raw)
                    assert raw["save"]["source"] == "print('CODE_STAYS')"
                    assert raw["task"]["items"][-1]["kind"] == "text"
            assert json.loads(db.get(PublicTask, public_id).items)[0]["kind"] == "text"
        with TestClient(migrated) as c:
            c.cookies.update(client.cookies)
            current = c.get("/api/play/project", headers=h).json()
            assert secret not in json.dumps(current)
            assert current["save"]["source"] == "print('CODE_STAYS')"
            response = c.get(f"/api/teacher/submissions/{sid}/versions/2")
            assert response.status_code == 200
            assert secret not in response.text
            downloaded = c.get(f"/api/teacher/submissions/{sid}/versions/2/download")
            with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
                assert secret not in archive.read("project.json").decode()
                assert archive.read("main.py") == b"print('CODE_STAYS')"
            copied = c.post(f"/api/teacher/gallery/{public_id}/copy", json={}, headers=th)
            assert copied.status_code == 200
            items = c.get(f'/api/teacher/tasks/{copied.json()["task_id"]}').json()["task"]["items"]
            assert items[0]["kind"] == "text"
    finally:
        migrated.state.engine.dispose()
