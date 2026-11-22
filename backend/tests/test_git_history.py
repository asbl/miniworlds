from __future__ import annotations

import io
import shutil

import pytest

from .conftest import auth, create_project, student_token

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git nicht installiert")

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _save(client, token, source, message=None):
    body = {"source": source, "db": None, "base_revision": client.get("/api/play/project", headers=auth(token)).json()["revision"]}
    if message is not None:
        body["message"] = message
    r = client.put("/api/play/save", json=body, headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _history(client, token):
    r = client.get("/api/play/history", headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


@requires_git
def test_save_creates_commits_and_history(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    first = _save(client, token, "print('v1')", "Erste Version")
    assert first["commit"]
    second = _save(client, token, "print('v2')", "Zweite Version")
    assert second["commit"] and second["commit"] != first["commit"]
    # unveränderter Save erzeugt keinen neuen Commit
    assert _save(client, token, "print('v2')", "nochmal gleich") ["commit"] is None
    history = _history(client, token)
    assert history["available"] is True
    assert [c["message"] for c in history["commits"]] == ["Zweite Version", "Erste Version"]
    assert all(c["hash"] and c["short"] and c["date"] for c in history["commits"])


@requires_git
def test_history_detail_shows_diff(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _save(client, token, "a = 1", "Erste Version")
    _save(client, token, "a = 2", "Zweite Version")
    top = _history(client, token)["commits"][0]
    r = client.get(f"/api/play/history/{top['hash']}", headers=auth(token))
    assert r.status_code == 200, r.text
    assert "Zweite Version" in r.json()["show"]
    assert "-a = 1" in r.json()["show"] and "+a = 2" in r.json()["show"]
    # ungültiger Commit-Bezeichner
    assert client.get("/api/play/history/kein..commit", headers=auth(token)).status_code == 404
    # ohne Token nicht erreichbar
    assert client.get("/api/play/history").status_code == 401


@requires_git
def test_restore_version_sets_save_and_adds_commit(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _save(client, token, "a = 1", "Erste Version")
    _save(client, token, "a = 2", "Zweite Version")
    commits = _history(client, token)["commits"]
    old_hash = commits[1]["hash"]
    r = client.post(f"/api/play/restore/{old_hash}?base_revision=2", headers=auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["save"]["source"] == "a = 1"
    assert r.json()["commit"]
    # aktueller Save im Projekt steht auf der wiederhergestellten Version
    proj = client.get("/api/play/project", headers=auth(token)).json()
    assert proj["save"]["source"] == "a = 1"
    # und der Verlauf bleibt lückenlos (Restore ist selbst ein Commit)
    messages = [c["message"] for c in _history(client, token)["commits"]]
    assert messages[0].startswith("Wiederhergestellt:")
    assert messages[1:] == ["Zweite Version", "Erste Version"]


@requires_git
def test_restore_unknown_commit_and_read_only(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _save(client, token, "a = 1", "Erste Version")
    assert client.post("/api/play/restore/0000000", headers=auth(token)).status_code == 404
    client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": teacher_csrf})
    commits = _history(client, token)["commits"]
    assert client.post(f"/api/play/restore/{commits[0]['hash']}", headers=auth(token)).status_code == 403


@requires_git
def test_media_upload_and_delete_are_committed(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    _save(client, token, "a = 1", "Erste Version")
    r = client.post(
        "/api/play/media",
        headers=auth(token),
        files={"file": ("bild.png", io.BytesIO(PNG), "application/octet-stream")},
        data={"license": "CC0", "source": "eigenes Foto"},
    )
    assert r.status_code == 200, r.text
    mid = r.json()["media"]["id"]
    messages = [c["message"] for c in _history(client, token)["commits"]]
    assert any("bild.png" in m for m in messages)
    client.delete(f"/api/play/media/{mid}", headers=auth(token))
    messages = [c["message"] for c in _history(client, token)["commits"]]
    assert any("gelöscht" in m for m in messages)


def test_without_git_save_still_works_and_history_reports_unavailable(client, teacher_csrf, monkeypatch):
    from app import gitstore

    monkeypatch.setattr(gitstore, "git_available", lambda: False)
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    r = _save(client, token, "print('v1')", "Erste Version")
    assert r["ok"] is True and r["commit"] is None
    history = _history(client, token)
    assert history["available"] is False and history["commits"] == []
    # Restore meldet sauber 503 statt zu fehlschlagen
    assert client.post("/api/play/restore/abcdef1", headers=auth(token)).status_code == 503
