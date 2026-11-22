from __future__ import annotations

from .conftest import auth, create_project, make_teacher, student_token


def _mk_task(client, csrf, title="Aufgabe 1", template=False):
    r = client.post("/api/teacher/tasks", json={"title": title, "description": "Beschreibung", "is_template_for_new_projects": template}, headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200, r.text
    return r.json()["task"]["id"]


def _add_item(client, csrf, tid, kind, prompt):
    r = client.post(f"/api/teacher/tasks/{tid}/items", json={"kind": kind, "prompt": prompt}, headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200, r.text
    return r.json()["item"]["id"]


def test_task_crud(client, teacher_csrf):
    tid = _mk_task(client, teacher_csrf)
    i1 = _add_item(client, teacher_csrf, tid, "text", "Lies Kapitel 3")
    i2 = _add_item(client, teacher_csrf, tid, "checkbox", "Beispiel ausprobiert")
    _add_item(client, teacher_csrf, tid, "text", "Baue das Beispiel nach")
    r = client.get(f"/api/teacher/tasks/{tid}", headers={"X-CSRF-Token": teacher_csrf})
    assert [i["kind"] for i in r.json()["task"]["items"]] == ["text", "checkbox", "text"]
    r = client.patch(f"/api/teacher/tasks/{tid}/items/{i2}", json={"prompt": "Beispiel nachgebaut"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.json()["item"]["prompt"] == "Beispiel nachgebaut"
    r = client.delete(f"/api/teacher/tasks/{tid}/items/{i1}", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    r = client.get(f"/api/teacher/tasks/{tid}", headers={"X-CSRF-Token": teacher_csrf})
    assert len(r.json()["task"]["items"]) == 2
    r = client.post(f"/api/teacher/tasks/{tid}/items", json={"kind": "bogus", "prompt": "x"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 400


def test_assign_submit_flow(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    tid = _mk_task(client, teacher_csrf)
    cb = _add_item(client, teacher_csrf, tid, "checkbox", "Erledigt")
    ta = _add_item(client, teacher_csrf, tid, "checkbox", "Programm getestet")

    r = client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.json()["created"] == 1
    # Doppel-Zuweisung erzeugt nichts Neues
    r = client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.json()["created"] == 0

    token = student_token(client, p["code"])
    r = client.get("/api/play/project", headers=auth(token))
    tasks = r.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["status"] == "open"
    aid = tasks[0]["assignment_id"]

    answers = {str(cb): {"checked": True}, str(ta): {"checked": True}}
    r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": answers}, headers=auth(token))
    assert r.status_code == 200 and r.json()["version"] == 1

    r = client.post(f"/api/play/tasks/{aid}/submit", json={}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["status"] == "submitted"

    # nach Abgabe: Entwurf gesperrt, erneute Abgabe 409
    r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": answers}, headers=auth(token))
    assert r.status_code == 409
    r = client.post(f"/api/play/tasks/{aid}/submit", json={}, headers=auth(token))
    assert r.status_code == 409

    # Lehrer sieht Abgabe in der Matrix
    r = client.get(f"/api/teacher/tasks/{tid}/submissions", headers={"X-CSRF-Token": teacher_csrf})
    subs = r.json()["submissions"]
    assert subs[0]["status"] == "submitted"
    assert subs[0]["answers"][str(cb)] == {"checked": True}
    assert subs[0]["code"] == p["code"]

    # Lehrer markiert erledigt, ohne Freitext-Rückmeldung
    r = client.get(f"/api/teacher/tasks/{tid}/submissions", headers={"X-CSRF-Token": teacher_csrf})
    aid2 = r.json()["submissions"][0]["assignment_id"]
    r = client.patch(f"/api/teacher/submissions/{aid2}", json={"done": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200 and r.json()["done"] is True

    # Lehrer öffnet wieder → Schüler kann neue Version abgeben
    r = client.post(f"/api/teacher/submissions/{aid2}/reopen", json={}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    answers2 = {str(cb): {"checked": True}, str(ta): {"checked": False}}
    r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": answers2, "base_version": 2}, headers=auth(token))
    assert r.status_code == 200 and r.json()["version"] == 3  # 1 Entwurf, 2 submitted, 3 neuer Entwurf
    r = client.post(f"/api/play/tasks/{aid}/submit", json={}, headers=auth(token))
    assert r.status_code == 200 and r.json()["version"] == 4


def test_read_only_blocks_submit(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    tid = _mk_task(client, teacher_csrf)
    _add_item(client, teacher_csrf, tid, "checkbox", "x")
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers={"X-CSRF-Token": teacher_csrf})
    token = student_token(client, p["code"])
    aid = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]["assignment_id"]
    client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {}}, headers=auth(token)).status_code == 403
    assert client.post(f"/api/play/tasks/{aid}/submit", json={}, headers=auth(token)).status_code == 403


def test_template_task_auto_assigned_to_new_projects(client, teacher_csrf):
    tid = _mk_task(client, teacher_csrf, template=True)
    _add_item(client, teacher_csrf, tid, "text", "Hallo")
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    tasks = client.get("/api/play/project", headers=auth(token)).json()["tasks"]
    assert len(tasks) == 1 and tasks[0]["task_id"] == tid


def test_assign_all(client, teacher_csrf):
    create_project(client, teacher_csrf, count=3)
    tid = _mk_task(client, teacher_csrf)
    _add_item(client, teacher_csrf, tid, "text", "t")
    r = client.post(f"/api/teacher/tasks/{tid}/assign", json={"all": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.json()["created"] == 3
    r = client.get(f"/api/teacher/tasks/{tid}", headers={"X-CSRF-Token": teacher_csrf})
    assert r.json()["task"]["is_template_for_new_projects"] is True
    assert len(r.json()["task"]["assignments"]) == 3
    # neues Projekt bekommt die Template-Aufgabe automatisch
    p4 = create_project(client, teacher_csrf)[0]
    token = student_token(client, p4["code"])
    assert len(client.get("/api/play/project", headers=auth(token)).json()["tasks"]) == 1


def test_answers_count_toward_quota(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    tid = _mk_task(client, teacher_csrf)
    cb = _add_item(client, teacher_csrf, tid, "checkbox", "Erledigt")
    headers = {"X-CSRF-Token": teacher_csrf}
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers=headers)
    token = student_token(client, p["code"])
    aid = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]["assignment_id"]
    r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(cb): {"checked": True}}}, headers=auth(token))
    assert r.status_code == 200
    client.patch(f"/api/teacher/projects/{p['id']}", json={"quota_bytes": 1}, headers=headers)
    r = client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(cb): {"checked": False}}, "base_version": 1}, headers=auth(token))
    assert r.status_code == 413


def test_task_isolation_between_teachers(client, client2, admin_csrf):
    t1 = make_teacher(client, email="t1@schule.de")
    p1 = create_project(client, t1)[0]
    tid1 = _mk_task(client, t1)
    _add_item(client, t1, tid1, "text", "nur t1")
    client.post(f"/api/teacher/tasks/{tid1}/assign", json={"project_ids": [p1["id"]]}, headers={"X-CSRF-Token": t1})
    t2 = make_teacher(client2, email="t2@schule.de")
    assert client2.get(f"/api/teacher/tasks/{tid1}", headers={"X-CSRF-Token": t2}).status_code == 404
    assert client2.get(f"/api/teacher/tasks/{tid1}/submissions", headers={"X-CSRF-Token": t2}).status_code == 404
    r = client2.get("/api/teacher/tasks", headers={"X-CSRF-Token": t2})
    assert r.json()["tasks"] == []
