from __future__ import annotations

from datetime import timedelta

from .conftest import login, make_teacher


def test_invite_code_check_rate_limited(client, admin_csrf):
    r = client.post("/api/admin/invites", json={"school": "S"}, headers={"X-CSRF-Token": admin_csrf})
    code = r.json()["code"]
    last = None
    for _ in range(25):
        last = client.post("/api/auth/invite-code-check", json={"invite_code": code, "email": "", "password": ""})
    assert last.status_code == 429


def test_login_per_account_rate_limited(client):
    # 5 Fehlversuche für denselben Account erlaubt, dann 429 — egal welcher IP-Eindruck
    statuses = [
        client.post("/api/auth/login", json={"email": "admin@schule.de", "password": "falsch", "role": "admin"}).status_code
        for _ in range(6)
    ]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


def test_expired_sessions_cleaned_on_login(client, app):
    from app.models import Session as DbSession
    from app.models import utcnow
    from app.security import hash_token

    db = app.state.SessionLocal()
    try:
        db.add(DbSession(user_id=1, token_hash=hash_token("abgelaufen"), expires_at=utcnow() - timedelta(hours=1)))
        db.commit()
        assert db.query(DbSession).count() == 1
    finally:
        db.close()
    login(client, "admin@schule.de", "adminpw123", "admin")
    db = app.state.SessionLocal()
    try:
        # abgelaufene Session wurde beim Login entfernt, neue ist drin
        assert db.query(DbSession).filter_by(token_hash=hash_token("abgelaufen")).count() == 0
        assert db.query(DbSession).count() == 1
    finally:
        db.close()


def test_no_user_enumeration_on_login(client):
    r1 = client.post("/api/auth/login", json={"email": "gibtsnicht@schule.de", "password": "x", "role": "admin"})
    r2 = client.post("/api/auth/login", json={"email": "admin@schule.de", "password": "x", "role": "admin"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


def test_student_token_not_accepted_for_teacher_api(client, client2, teacher_csrf):
    # Schüler-Bearer-Token allein (ohne Session-Cookie) darf keine Lehrer-Routen öffnen
    from .conftest import create_project, student_token

    tok = student_token(client, create_project(client, teacher_csrf)[0]["code"])
    r = client2.get("/api/teacher/projects", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
