from __future__ import annotations

import io

from .conftest import auth, create_project, student_token

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
TXT = b"hello world, not an image"


def _upload(client, token, content, filename, **fields):
    return client.post(
        "/api/play/media",
        headers=auth(token),
        files={"file": (filename, io.BytesIO(content), "application/octet-stream")},
        data=fields,
    )


def test_upload_list_serve_delete(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    r = _upload(client, token, PNG, "bild.png", license="CC0", source="eigenes Foto")
    assert r.status_code == 200, r.text
    mid = r.json()["media"]["id"]

    r = client.get("/api/play/project", headers=auth(token))
    assert len(r.json()["media"]) == 1
    assert r.json()["media"][0]["license"] == "CC0"
    assert r.json()["used_bytes"] >= len(PNG)

    r = client.get(f"/api/play/media/{mid}/file", headers=auth(token))
    assert r.status_code == 200 and r.content == PNG
    # ohne Token nicht erreichbar
    assert client.get(f"/api/play/media/{mid}/file").status_code == 401

    # Lizenz ändern
    r = client.patch(f"/api/play/media/{mid}", json={"license": "CC-BY", "license_text": "", "source": "unsplash"}, headers=auth(token))
    assert r.status_code == 200 and r.json()["media"]["license"] == "CC-BY"

    r = client.delete(f"/api/play/media/{mid}", headers=auth(token))
    assert r.status_code == 200
    assert client.get("/api/play/project", headers=auth(token)).json()["media"] == []


def test_upload_rejects_wrong_type_and_fake_magic(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    # Endung nicht erlaubt
    assert _upload(client, token, TXT, "evil.exe").status_code == 400
    # Endung ok, Inhalt falsch
    assert _upload(client, token, TXT, "fake.png").status_code == 400


def test_upload_counts_toward_quota(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.patch(f"/api/teacher/projects/{p['id']}", json={"quota_bytes": len(PNG) + 10}, headers={"X-CSRF-Token": teacher_csrf})
    r = _upload(client, token, PNG, "a.png")
    assert r.status_code == 200
    r = _upload(client, token, PNG, "b.png")
    assert r.status_code == 413


def test_read_only_blocks_media(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.patch(f"/api/teacher/projects/{p['id']}", json={"read_only": True}, headers={"X-CSRF-Token": teacher_csrf})
    assert _upload(client, token, PNG, "a.png").status_code == 403
