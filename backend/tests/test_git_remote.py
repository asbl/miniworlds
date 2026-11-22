from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from .conftest import auth, create_project, student_token

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git nicht installiert")


@pytest.fixture(autouse=True)
def public_git_dns(monkeypatch):
    from app import gitstore
    monkeypatch.setattr(gitstore.socket, "getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))])


def _save(client, token, source, message=None):
    body = {"source": source, "db": None, "base_revision": client.get("/api/play/project", headers=auth(token)).json()["revision"]}
    if message is not None:
        body["message"] = message
    r = client.put("/api/play/save", json=body, headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _make_bare(tmp_path, name="remote.git") -> Path:
    bare = tmp_path / name
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
    return bare


def test_validate_remote_url_rules():
    from app import gitstore

    # erlaubt: https + ssh
    assert gitstore.validate_remote_url("https://github.com/user/repo.git") == "https://github.com/user/repo.git"
    assert gitstore.validate_remote_url("git@github.com:user/repo.git") == "git@github.com:user/repo.git"
    # verboten: http, file, Credentials in URL, private IPs, Whitelist-Verstoß
    for bad in ("http://github.com/u/r.git", "file:///etc/passwd", "/tmp/evil.git",
                "https://user:pass@github.com/u/r.git", "https://127.0.0.1/x.git",
                "https://192.168.1.10/x.git", "https://169.254.169.254/x.git"):
        with pytest.raises(gitstore.GitError):
            gitstore.validate_remote_url(bad)
    with pytest.raises(gitstore.GitError):
        gitstore.validate_remote_url("https://gitlab.com/u/r.git", allowed_hosts="github.com")
    assert gitstore.validate_remote_url("https://git.schule.de/u/r.git", allowed_hosts="github.com,git.schule.de")
    # "local" erlaubt Datei-Pfade (nur Tests)
    assert gitstore.validate_remote_url("/tmp/remote.git", allowed_hosts="local").startswith("/tmp/")


@requires_git
def test_remote_set_get_delete_and_token_never_leaks(client, teacher_csrf, tmp_path):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])

    # ungültige URL → 400 mit deutscher Meldung (http und Credentials in URL sind immer verboten)
    for bad in ("http://github.com/u/r.git", "https://user:pass@github.com/u/r.git"):
        r = client.put("/api/play/remote", json={"url": bad}, headers=auth(token))
        assert r.status_code == 400, (bad, r.status_code, r.text)

    r = client.put("/api/play/remote", json={"url": "https://github.com/klasse/abgaben.git", "token": "ghp_supersecret"}, headers=auth(token))
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "url": "https://github.com/klasse/abgaben.git", "has_token": True}

    r = client.get("/api/play/remote", headers=auth(token))
    data = r.json()
    assert data == {"configured": True, "url": "https://github.com/klasse/abgaben.git", "has_token": True}
    assert "ghp_supersecret" not in r.text

    # Token landet weder in .git/config noch in der Remote-URL
    settings = client.app.state.settings
    from app import gitstore

    repo = gitstore.repo_dir(settings, p["id"])
    assert gitstore.remote_url(settings, p["id"]) == "https://github.com/klasse/abgaben.git"
    config_text = (repo / ".git" / "config").read_text(encoding="utf-8")
    assert "ghp_supersecret" not in config_text

    r = client.delete("/api/play/remote", headers=auth(token))
    assert r.status_code == 200
    assert client.get("/api/play/remote", headers=auth(token)).json()["configured"] is False
    assert gitstore.remote_url(settings, p["id"]) is None
    # Token-Zeile ist aus der DB verschwunden
    from app.models import ProjectRemote

    session = client.app.state.SessionLocal()
    try:
        assert session.get(ProjectRemote, p["id"]) is None
    finally:
        session.close()


@requires_git
def test_push_and_pull_against_local_bare_repo(client, teacher_csrf, tmp_path):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    bare = _make_bare(tmp_path)

    # ohne Remote → sauberer 409
    assert client.post("/api/play/push", headers=auth(token)).status_code == 409

    r = client.put("/api/play/remote", json={"url": str(bare)}, headers=auth(token))
    assert r.status_code == 200, r.text

    _save(client, token, "a = 1\n", "Erste Version")
    r = client.post("/api/play/push", headers=auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True and r.json()["url"] == str(bare)
    # im bare Repo liegt der Commit
    log = subprocess.run(["git", "-C", str(bare), "log", "--oneline"], capture_output=True, text=True)
    assert "Erste Version" in log.stdout

    # Fremder Commit im Remote (z. B. Lehrkraft oder zweites Gerät)
    other = tmp_path / "other"
    subprocess.run(["git", "clone", str(bare), str(other)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(other), "config", "user.name", "Lehrer"], check=True)
    subprocess.run(["git", "-C", str(other), "config", "user.email", "l@schule.de"], check=True)
    (other / "main.py").write_text("a = 2\n# Lehrkraft\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(other), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(other), "commit", "-m", "Korrektur durch Lehrkraft"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(other), "push", "origin", "HEAD"], check=True, capture_output=True)

    r = client.post("/api/play/pull?base_revision=1", headers=auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["save"]["source"] == "a = 2\n# Lehrkraft\n"
    # Save in der DB und Verlauf sind synchron
    proj = client.get("/api/play/project", headers=auth(token)).json()
    assert proj["save"]["source"] == "a = 2\n# Lehrkraft\n"
    messages = [c["message"] for c in client.get("/api/play/history", headers=auth(token)).json()["commits"]]
    assert "Korrektur durch Lehrkraft" in messages


@requires_git
def test_pull_blocked_when_read_only_and_push_allowed(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    bare = _make_bare(client.app.state.settings.git_root and Path(client.app.state.settings.git_root).parent / "bare-ro.git")
    client.put("/api/play/remote", json={"url": str(bare)}, headers=auth(token))
    _save(client, token, "a = 1\n", "Erste Version")
    client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert client.post("/api/play/pull?base_revision=1", headers=auth(token)).status_code == 403
    assert client.post("/api/play/push", headers=auth(token)).status_code == 200  # Push ändert lokalen Save nicht
    assert client.put("/api/play/remote", json={"url": str(bare)}, headers=auth(token)).status_code == 403


@requires_git
def test_teacher_sets_class_remote_and_student_pushes(client, teacher_csrf, tmp_path):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    bare = _make_bare(tmp_path)

    r = client.put(f"/api/teacher/projects/{p['id']}/remote", json={"url": str(bare), "token": "deploy-token-123"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200, r.text
    assert r.json()["has_token"] is True

    # Schüler sieht Remote, Token bleibt verborgen
    data = client.get("/api/play/remote", headers=auth(token)).json()
    assert data["configured"] is True and data["url"] == str(bare) and data["has_token"] is True
    assert "deploy-token-123" not in client.get("/api/play/remote", headers=auth(token)).text

    _save(client, token, "abgabe = True\n", "Abgabe")
    r = client.post("/api/play/push", headers=auth(token))
    assert r.status_code == 200, r.text
    log = subprocess.run(["git", "-C", str(bare), "log", "--oneline"], capture_output=True, text=True)
    assert "Abgabe" in log.stdout

    # Aufräumen durch Lehrer
    r = client.delete(f"/api/teacher/projects/{p['id']}/remote", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert client.get("/api/play/remote", headers=auth(token)).json()["configured"] is False


def test_askpass_supplies_token_without_argv():
    from app import gitstore

    with gitstore._askpass("secret-token-42") as env:
        script = env["GIT_ASKPASS"]
        pw = subprocess.run([script, "Password for 'https://github.com': "], capture_output=True, text=True, env=env)
        user = subprocess.run([script, "Username for 'https://github.com': "], capture_output=True, text=True, env=env)
        assert pw.stdout.strip() == "secret-token-42"
        assert user.stdout.strip() == "x-access-token"
    with gitstore._askpass(None) as env:
        assert env["GIT_TERMINAL_PROMPT"] == "0" and "GIT_ASKPASS" not in env
