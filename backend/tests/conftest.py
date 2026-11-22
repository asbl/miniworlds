from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


WHEEL = Path(__file__).resolve().parents[1] / "app" / "static" / "wheel" / "miniworlds.whl"


@pytest.fixture()
def settings(tmp_path):
    return Settings(
        secret_key="test-secret",
        database_url=f"sqlite:///{tmp_path}/test.db",
        media_root=str(tmp_path / "media"),
        git_root=str(tmp_path / "git"),
        git_allowed_hosts="local,github.com",  # Tests dürfen lokale bare Repos als Remote nutzen
        admin_email="admin@schule.de",
        admin_password="adminpw123",
        base_url="http://test",
        cookie_secure=False,
        session_hours=1,
        student_token_hours=1,
        miniworlds_wheel_path=str(WHEEL) if WHEEL.exists() else "",
    )


@pytest.fixture()
def app(settings):
    return create_app(settings, enable_yearly_task=False)


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client2(app):
    with TestClient(app) as c:
        yield c


def login(client, email, password, role):
    r = client.post("/api/auth/login", json={"email": email, "password": password, "role": role})
    assert r.status_code == 200, r.text
    return r.json()["csrf"]


@pytest.fixture()
def admin_csrf(client):
    return login(client, "admin@schule.de", "adminpw123", "admin")


def make_teacher(client, email="lehrer@schule.de", school="Testschule", invite_email=None):
    """Legt per frischem Admin-Login einen Invite an und löst ihn ein. Client-Session ist danach die des Lehrers."""
    admin_csrf = login(client, "admin@schule.de", "adminpw123", "admin")
    payload = {"school": school}
    if invite_email:
        payload["email"] = invite_email
    r = client.post("/api/admin/invites", json=payload, headers={"X-CSRF-Token": admin_csrf})
    assert r.status_code == 200, r.text
    code = r.json()["code"]
    r = client.post("/api/auth/claim", json={"invite_code": code, "email": email, "password": "lehrerpw123"})
    assert r.status_code == 200, r.text
    return r.json()["csrf"]


@pytest.fixture()
def teacher_csrf(client):
    return make_teacher(client)


def create_project(client, teacher_csrf, count=1):
    r = client.post("/api/teacher/projects", json={"count": count}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200, r.text
    return r.json()["projects"]


def student_token(client, code):
    r = client.post("/api/claim", json={"code": code})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
