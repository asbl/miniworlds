from __future__ import annotations

import io

from .conftest import auth, create_project, make_teacher, student_token

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _setup(client, teacher_csrf, source="print('v1')"):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.put("/api/play/save", json={"source": source, "db": None}, headers=auth(token))
    client.post(
        "/api/play/media",
        headers=auth(token),
        files={"file": ("bild.png", io.BytesIO(PNG), "application/octet-stream")},
        data={"license": "CC0", "license_text": "", "source": "eigen"},
    )
    return p, token


def test_share_full_flow_and_snapshot_immutable(client, teacher_csrf):
    p, token = _setup(client, teacher_csrf)
    # Antrag ohne Erklärung abgelehnt
    r = client.post("/api/play/share-request", json={"declaration_accepted": False}, headers=auth(token))
    assert r.status_code == 400
    r = client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token))
    assert r.status_code == 200
    rid = r.json()["id"]
    # doppelter Antrag → 409
    assert client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token)).status_code == 409

    # Lehrer sieht Antrag mit Medien/Lizenzen
    r = client.get("/api/teacher/share-requests", headers={"X-CSRF-Token": teacher_csrf})
    reqs = r.json()["requests"]
    assert reqs[0]["id"] == rid and reqs[0]["status"] == "pending"
    assert reqs[0]["media"][0]["license"] == "CC0"
    assert reqs[0]["code"] == p["code"]

    # Freigeben mit Custom-Slug
    r = client.post(f"/api/teacher/share-requests/{rid}/approve", json={"slug": "Mein-Spiel"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200, r.text
    assert r.json()["url"] == "/p/mein-spiel"

    # Öffentliche Seite + Payload ohne Login
    r = client.get("/p/mein-spiel")
    assert r.status_code == 200 and "Mein-Spiel".lower() in r.text.lower() or "mein-spiel" in r.text
    r = client.get("/api/public/mein-spiel")
    assert r.status_code == 200
    payload = r.json()
    assert payload["save"]["source"] == "print('v1')"
    assert payload["media"][0]["license"] == "CC0"
    mid = payload["media"][0]["asset_id"]
    r = client.get(f"/api/public/mein-spiel/media/{mid}")
    assert r.status_code == 200 and r.content == PNG

    # Schüler ändert danach → Snapshot bleibt eingefroren
    client.put("/api/play/save", json={"source": "print('v2-geändert')", "db": None}, headers=auth(token))
    payload2 = client.get("/api/public/mein-spiel").json()
    assert payload2["save"]["source"] == "print('v1')"

    # Widerruf → Seite weg
    r = client.post(f"/api/teacher/share-requests/{rid}/revoke", json={}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert client.get("/p/mein-spiel").status_code == 404
    assert client.get("/api/public/mein-spiel").status_code == 404

    # Audit
    r = client.get("/api/teacher/audit", headers={"X-CSRF-Token": teacher_csrf})
    actions = [e["action"] for e in r.json()["entries"]]
    assert "share_approved" in actions and "share_revoked" in actions


def test_share_slug_conflict_and_validation(client, teacher_csrf):
    p1, token1 = _setup(client, teacher_csrf)
    p2, token2 = _setup(client, teacher_csrf)
    client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token1))
    client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token2))
    r = client.get("/api/teacher/share-requests", headers={"X-CSRF-Token": teacher_csrf})
    ids = [x["id"] for x in r.json()["requests"]]
    r = client.post(f"/api/teacher/share-requests/{ids[0]}/approve", json={"slug": "doppelt"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    r = client.post(f"/api/teacher/share-requests/{ids[1]}/approve", json={"slug": "doppelt"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 409
    r = client.post(f"/api/teacher/share-requests/{ids[1]}/approve", json={"slug": "Bad_Slug!"}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 400


def test_share_reject_and_isolation(client, client2, admin_csrf):
    t1 = make_teacher(client, email="t1@schule.de")
    p1, token1 = _setup(client, t1)
    client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token1))
    t2 = make_teacher(client2, email="t2@schule.de")
    # t2 sieht den Antrag nicht und kann nicht entscheiden
    r = client2.get("/api/teacher/share-requests", headers={"X-CSRF-Token": t2})
    assert r.json()["requests"] == []
    rid = client.get("/api/teacher/share-requests", headers={"X-CSRF-Token": t1}).json()["requests"][0]["id"]
    assert client2.post(f"/api/teacher/share-requests/{rid}/approve", json={"slug": "x-1"}, headers={"X-CSRF-Token": t2}).status_code == 404
    r = client.post(f"/api/teacher/share-requests/{rid}/reject", json={}, headers={"X-CSRF-Token": t1})
    assert r.status_code == 200


def test_public_report_logged(client, client2, teacher_csrf):
    from .conftest import login

    p, token = _setup(client, teacher_csrf)
    client.post("/api/play/share-request", json={"declaration_accepted": True}, headers=auth(token))
    rid = client.get("/api/teacher/share-requests", headers={"X-CSRF-Token": teacher_csrf}).json()["requests"][0]["id"]
    client.post(f"/api/teacher/share-requests/{rid}/approve", json={"slug": "melden-test"}, headers={"X-CSRF-Token": teacher_csrf})
    r = client.post("/api/public/melden-test/report", json={"reason": "urheberrechtlich bedenklich"})
    assert r.status_code == 200
    admin2 = login(client2, "admin@schule.de", "adminpw123", "admin")
    r = client2.get("/api/admin/audit", headers={"X-CSRF-Token": admin2})
    assert any(e["action"] == "public_report" for e in r.json()["entries"])
