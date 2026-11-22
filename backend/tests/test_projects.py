from __future__ import annotations

from .conftest import auth, create_project, login, make_teacher, student_token


def test_create_batch_codes_unique(client, teacher_csrf):
    projects = create_project(client, teacher_csrf, count=5)
    codes = [p["code"] for p in projects]
    assert len(set(codes)) == 5
    assert all(len(c) == 10 for c in codes)


def test_student_claim_and_save(client, teacher_csrf):
    code = create_project(client, teacher_csrf)[0]["code"]
    token = student_token(client, code)
    r = client.get("/api/play/project", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["save"] is None
    r = client.put("/api/play/save", json={"source": "print('hi')", "db": None}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["used_bytes"] > 0
    r = client.get("/api/play/project", headers=auth(token))
    assert r.json()["save"]["source"] == "print('hi')"
    r = client.get("/api/play/download", headers=auth(token))
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]


def test_quota_enforced_on_save(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    r = client.patch(f"/api/teacher/projects/{p['id']}", json={"quota_bytes": 200}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    r = client.put("/api/play/save", json={"source": "x" * 100}, headers=auth(token))
    assert r.status_code == 200
    r = client.put("/api/play/save", json={"source": "x" * 500}, headers=auth(token))
    assert r.status_code == 413


def test_quota_cap_from_admin_settings(client, client2, admin_csrf, teacher_csrf):
    # teacher_csrf ist auf client eingeloggt; Admin auf client2
    admin2 = login(client2, "admin@schule.de", "adminpw123", "admin")
    r = client2.patch("/api/admin/settings", json={"teacher_quota_cap": 1000}, headers={"X-CSRF-Token": admin2})
    assert r.status_code == 200
    p = create_project(client, teacher_csrf)[0]
    r = client.patch(f"/api/teacher/projects/{p['id']}", json={"quota_bytes": 2000}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 400
    r = client.patch(f"/api/teacher/projects/{p['id']}", json={"quota_bytes": 1000}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert r.json()["project"]["quota_bytes"] == 1000


def test_read_only_blocks_save_but_allows_view(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.put("/api/play/save", json={"source": "a = 1"}, headers=auth(token))
    r = client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    r = client.put("/api/play/save", json={"source": "a = 2"}, headers=auth(token))
    assert r.status_code == 403
    assert client.get("/api/play/project", headers=auth(token)).status_code == 200
    assert client.get("/api/play/download", headers=auth(token)).status_code == 200
    # Reaktivierung durch Lehrer
    client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": False}, headers={"X-CSRF-Token": teacher_csrf})
    r = client.put("/api/play/save", json={"source": "a = 3", "base_revision": 3}, headers=auth(token))
    assert r.status_code == 200


def test_regenerate_code_invalidates_old(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    old_token = student_token(client, p["code"])
    r = client.post(f"/api/teacher/projects/{p['id']}/regenerate-code", json={}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    new_code = r.json()["code"]
    assert new_code != p["code"]
    # alter Code und alter Token ungültig
    assert client.post("/api/claim", json={"code": p["code"]}).status_code == 401
    assert client.get("/api/play/project", headers=auth(old_token)).status_code == 401
    # neuer Code funktioniert
    new_token = student_token(client, new_code)
    assert client.get("/api/play/project", headers=auth(new_token)).status_code == 200
    # Audit-Eintrag vorhanden
    r = client.get("/api/teacher/audit", headers={"X-CSRF-Token": teacher_csrf})
    assert any(e["action"] == "code_regenerated" for e in r.json()["entries"])


def test_teacher_isolation(client, client2, admin_csrf):
    t1 = make_teacher(client, email="t1@schule.de")  # client-Session = t1
    p = create_project(client, t1)[0]
    t2 = make_teacher(client2, email="t2@schule.de")  # client2-Session = t2
    assert client2.get(f"/api/teacher/projects/{p['id']}", headers={"X-CSRF-Token": t2}).status_code == 404
    assert client2.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": t2}).status_code == 404
    assert client2.post(f"/api/teacher/projects/{p['id']}/regenerate-code", json={}, headers={"X-CSRF-Token": t2}).status_code == 404
    # t2 sieht das Projekt nicht in seiner Liste
    r = client2.get("/api/teacher/projects", headers={"X-CSRF-Token": t2})
    assert all(x["id"] != p["id"] for x in r.json()["projects"])


def test_delete_project_invalidates_access(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.put("/api/play/save", json={"source": "x"}, headers=auth(token))
    r = client.delete(f"/api/teacher/projects/{p['id']}", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert client.post("/api/claim", json={"code": p["code"]}).status_code == 401
    assert client.get("/api/play/project", headers=auth(token)).status_code == 401


def test_code_reveal_endpoint(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    r = client.get(f"/api/teacher/projects/{p['id']}/code", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert r.json()["code"] == p["code"]


def test_claim_unknown_code(client):
    assert client.post("/api/claim", json={"code": "ZZZZZZZZZZ"}).status_code == 401
