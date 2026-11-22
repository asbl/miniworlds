from __future__ import annotations

from .conftest import login, make_teacher


def test_admin_login_ok(client):
    r = client.post("/api/auth/login", json={"email": "admin@schule.de", "password": "adminpw123", "role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert "session" in r.cookies


def test_admin_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "admin@schule.de", "password": "falsch", "role": "admin"})
    assert r.status_code == 401


def test_role_mismatch_rejected(client):
    make_teacher(client)
    r = client.post("/api/auth/login", json={"email": "lehrer@schule.de", "password": "lehrerpw123", "role": "admin"})
    assert r.status_code == 401


def test_claim_flow_and_school_from_invite(client):
    csrf = make_teacher(client, email="l2@schule.de", school="Gymnasium X")
    r = client.get("/api/teacher/me", headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200
    assert r.json()["school"] == "Gymnasium X"
    assert r.json()["email"] == "l2@schule.de"


def test_invite_single_use(client, admin_csrf):
    r = client.post("/api/admin/invites", json={"school": "S"}, headers={"X-CSRF-Token": admin_csrf})
    code = r.json()["code"]
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": "a@schule.de", "password": "lehrerpw123"})
    assert r.status_code == 200
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": "b@schule.de", "password": "lehrerpw123"})
    assert r.status_code == 401


def test_invite_email_binding(client, admin_csrf):
    r = client.post("/api/admin/invites", json={"school": "S", "email": "fest@schule.de"}, headers={"X-CSRF-Token": admin_csrf})
    code = r.json()["code"]
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": "andere@schule.de", "password": "lehrerpw123"})
    assert r.status_code == 400
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": "fest@schule.de", "password": "lehrerpw123"})
    assert r.status_code == 200


def test_short_password_rejected(client, admin_csrf):
    r = client.post("/api/admin/invites", json={"school": "S"}, headers={"X-CSRF-Token": admin_csrf})
    code = r.json()["code"]
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": "x@schule.de", "password": "kurz"})
    assert r.status_code == 400


def test_disabled_teacher_cannot_login(client, client2, admin_csrf):
    make_teacher(client)
    # Admin meldet sich auf client2 an (client hat noch Lehrer-Session)
    admin2 = login(client2, "admin@schule.de", "adminpw123", "admin")
    r = client2.get("/api/admin/teachers", headers={"X-CSRF-Token": admin2})
    tid = r.json()["teachers"][0]["id"]
    r = client2.post(f"/api/admin/teachers/{tid}/disable", json={"disabled": True}, headers={"X-CSRF-Token": admin2})
    assert r.status_code == 200
    r = client2.post("/api/auth/login", json={"email": "lehrer@schule.de", "password": "lehrerpw123", "role": "teacher"})
    assert r.status_code == 401


def test_csrf_required_for_mutations(client, admin_csrf):
    r = client.post("/api/admin/invites", json={"school": "S"})  # ohne X-CSRF-Token
    assert r.status_code == 403
    r = client.post("/api/admin/invites", json={"school": "S"}, headers={"X-CSRF-Token": "falsch"})
    assert r.status_code == 403


def test_unauthenticated_api_401(client):
    assert client.get("/api/teacher/projects").status_code == 401
    assert client.get("/api/admin/invites").status_code == 401
    assert client.get("/api/play/project").status_code == 401


def test_pages_redirect_to_login(client):
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code in (302, 303) and "/admin/login" in r.headers["location"]
    r = client.get("/teacher", follow_redirects=False)
    assert r.status_code in (302, 303) and "/teacher/login" in r.headers["location"]
    assert client.get("/play").status_code == 200
    assert client.get("/healthz").json() == {"ok": True}
