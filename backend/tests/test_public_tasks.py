from __future__ import annotations

from .conftest import create_project, login, make_teacher


def _mk_task(client, csrf, title="Scratch-Aufgabe"):
    r = client.post("/api/teacher/tasks", json={"title": title, "description": "desc"}, headers={"X-CSRF-Token": csrf})
    return r.json()["task"]["id"]


def _add_item(client, csrf, tid, kind, prompt):
    client.post(f"/api/teacher/tasks/{tid}/items", json={"kind": kind, "prompt": prompt}, headers={"X-CSRF-Token": csrf})


def test_publish_gallery_copy(client, client2, admin_csrf):
    t1 = make_teacher(client, email="t1@schule.de")
    tid = _mk_task(client, t1)
    _add_item(client, t1, tid, "text", "Einführung")
    _add_item(client, t1, tid, "checkbox", "Projekt erstellt")

    # veröffentlichen
    r = client.post(f"/api/teacher/tasks/{tid}/publish", json={"author_alias": "Lehrer A", "license": "CC BY"}, headers={"X-CSRF-Token": t1})
    assert r.status_code == 200, r.text
    pt_id = r.json()["public_task"]["id"]

    # t2 sieht es in der Galerie
    t2 = make_teacher(client2, email="t2@schule.de")
    r = client2.get("/api/teacher/gallery", headers={"X-CSRF-Token": t2})
    assert len(r.json()["tasks"]) == 1
    assert r.json()["tasks"][0]["author_alias"] == "Lehrer A"
    r = client2.get(f"/api/teacher/gallery/{pt_id}", headers={"X-CSRF-Token": t2})
    assert [i["prompt"] for i in r.json()["task"]["items"]] == ["Einführung", "Projekt erstellt"]

    # kopieren
    r = client2.post(f"/api/teacher/gallery/{pt_id}/copy", json={}, headers={"X-CSRF-Token": t2})
    assert r.status_code == 200
    new_tid = r.json()["task_id"]
    r = client2.get(f"/api/teacher/tasks/{new_tid}", headers={"X-CSRF-Token": t2})
    assert len(r.json()["task"]["items"]) == 2

    # Kopie unabhängig: t2 ändert Titel → Galerie-Snapshot bleibt
    client2.patch(f"/api/teacher/tasks/{new_tid}", json={"title": "Umbenannt"}, headers={"X-CSRF-Token": t2})
    r = client2.get(f"/api/teacher/gallery/{pt_id}", headers={"X-CSRF-Token": t2})
    assert r.json()["task"]["title"] == "Scratch-Aufgabe"

    # Original editieren + erneut publishen → Version 2, Items aktualisiert
    _add_item(client, t1, tid, "text", "Weiterführende Aufgabe")
    r = client.post(f"/api/teacher/tasks/{tid}/publish", json={"author_alias": "Lehrer A"}, headers={"X-CSRF-Token": t1})
    assert r.json()["public_task"]["version"] == 2
    r = client2.get(f"/api/teacher/gallery/{pt_id}", headers={"X-CSRF-Token": t2})
    assert r.json()["task"]["items_count"] == 3


def test_unpublish_and_admin_hide(client, client2, admin_csrf):
    t1 = make_teacher(client, email="t1@schule.de")
    tid = _mk_task(client, t1)
    pt_id = client.post(f"/api/teacher/tasks/{tid}/publish", json={}, headers={"X-CSRF-Token": t1}).json()["public_task"]["id"]

    # unpublish durch Owner
    r = client.post(f"/api/teacher/public-tasks/{pt_id}/unpublish", json={}, headers={"X-CSRF-Token": t1})
    assert r.status_code == 200
    t2 = make_teacher(client2, email="t2@schule.de")
    assert client2.get("/api/teacher/gallery", headers={"X-CSRF-Token": t2}).json()["tasks"] == []

    # Admin: publish again, dann hide
    client.post(f"/api/teacher/tasks/{tid}/publish", json={}, headers={"X-CSRF-Token": t1})
    assert len(client2.get("/api/teacher/gallery", headers={"X-CSRF-Token": t2}).json()["tasks"]) == 1
    admin2 = login(client2, "admin@schule.de", "adminpw123", "admin")
    r = client2.post(f"/api/admin/public-tasks/{pt_id}/hide", json={"hidden": True}, headers={"X-CSRF-Token": admin2})
    assert r.status_code == 200
    # Admin sieht es in der Moderationsliste (noch als Admin-Session)
    r = client2.get("/api/admin/public-tasks", headers={"X-CSRF-Token": admin2})
    assert r.json()["public_tasks"][0]["status"] == "hidden"
    # Galerie leer, Kopieren gesperrt (wieder als Lehrer anmelden)
    t2b = login(client2, "t2@schule.de", "lehrerpw123", "teacher")
    assert client2.get("/api/teacher/gallery", headers={"X-CSRF-Token": t2b}).json()["tasks"] == []
    assert client2.post(f"/api/teacher/gallery/{pt_id}/copy", json={}, headers={"X-CSRF-Token": t2b}).status_code == 404


def test_no_submissions_in_public_task(client, teacher_csrf):
    tid = _mk_task(client, teacher_csrf)
    _add_item(client, teacher_csrf, tid, "checkbox", "Programm getestet")
    p = create_project(client, teacher_csrf)[0]
    client.post(f"/api/teacher/tasks/{tid}/assign", json={"project_ids": [p["id"]]}, headers={"X-CSRF-Token": teacher_csrf})
    from .conftest import student_token, auth

    token = student_token(client, p["code"])
    aid = client.get("/api/play/project", headers=auth(token)).json()["tasks"][0]["assignment_id"]
    item_id = client.get("/api/teacher/tasks", headers={"X-CSRF-Token": teacher_csrf}).json()["tasks"][0]["items"][0]["id"]
    client.put(f"/api/play/tasks/{aid}/answers", json={"answers": {str(item_id): {"checked": True}}}, headers=auth(token))
    pt_id = client.post(f"/api/teacher/tasks/{tid}/publish", json={}, headers={"X-CSRF-Token": teacher_csrf}).json()["public_task"]["id"]
    r = client.get(f"/api/teacher/gallery/{pt_id}", headers={"X-CSRF-Token": teacher_csrf})
    import json as _json

    assert "answers" not in _json.dumps(r.json())
