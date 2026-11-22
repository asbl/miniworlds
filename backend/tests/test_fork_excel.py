from __future__ import annotations

import io

from .conftest import auth, create_project, student_token

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def test_fork_copies_save_and_media(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p["code"])
    client.put("/api/play/save", json={"source": "print('schueler')", "db": "dbdata"}, headers=auth(token))
    client.post(
        "/api/play/media",
        headers=auth(token),
        files={"file": ("b.png", io.BytesIO(PNG), "application/octet-stream")},
        data={"license": "CC0", "source": "", "license_text": ""},
    )
    r = client.post(f"/api/teacher/projects/{p['id']}/fork", json={}, headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200, r.text
    fork = r.json()
    # Lehrer-Kopie hat eigenen Code und denselben Stand
    fork_token = student_token(client, fork["code"])
    d = client.get("/api/play/project", headers=auth(fork_token)).json()
    assert d["save"]["source"] == "print('schueler')"
    assert len(d["media"]) == 1 and d["media"][0]["license"] == "CC0"
    # Original unverändert; Lehrer kann Kopie bearbeiten (nicht read-only)
    r = client.put("/api/play/save", json={"source": "print('lehrer-edit')"}, headers=auth(fork_token))
    assert r.status_code == 200
    orig = client.get("/api/play/project", headers=auth(token)).json()
    assert orig["save"]["source"] == "print('schueler')"
    # Audit
    r = client.get("/api/teacher/audit", headers={"X-CSRF-Token": teacher_csrf})
    assert any(e["action"] == "project_forked" for e in r.json()["entries"])


def test_excel_export_contains_codes_no_names(client, teacher_csrf):
    ps = create_project(client, teacher_csrf, count=3)
    r = client.get("/api/teacher/projects.xlsx", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(r.content))
    ws = wb.active
    header = [c.value for c in ws[1]]
    assert header[0] == "Code"
    assert not any("name" in str(h).lower() for h in header if h)
    codes = {ws.cell(row=i, column=1).value for i in range(2, ws.max_row + 1)}
    assert codes == {p["code"] for p in ps}

    r = client.get("/api/teacher/projects.csv", headers={"X-CSRF-Token": teacher_csrf})
    assert r.status_code == 200 and ps[0]["code"] in r.text
