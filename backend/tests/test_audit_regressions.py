import io
import json
import subprocess
import threading

from fastapi.testclient import TestClient

from app import gitstore
from app.main import create_app

from .conftest import auth, create_project, student_token
from .test_git_remote import _make_bare, _save


def test_request_size_limits_apply_to_headers_and_chunked_uploads(client, settings):
    response = client.put("/api/play/save", content=b"{}", headers={"Content-Length": str(settings.max_request_bytes + 1)})
    assert response.status_code == 413
    response = client.post("/api/auth/login", content=iter([bytes(1024)] * 1025))
    assert response.status_code == 413
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_remote_symlink_is_rejected_before_replacing_repository(client, teacher_csrf, settings, tmp_path):
    project = create_project(client, teacher_csrf)[0]
    token = student_token(client, project["code"])
    bare = _make_bare(tmp_path)
    assert client.put("/api/play/remote", json={"url": str(bare)}, headers=auth(token)).status_code == 200
    _save(client, token, "safe = True\n")
    assert client.post("/api/play/push", headers=auth(token)).status_code == 200
    peer = tmp_path / "peer"
    subprocess.run(["git", "clone", str(bare), str(peer)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(peer), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(peer), "config", "user.email", "test@example.test"], check=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("unchanged")
    (peer / "main.py").unlink()
    (peer / "main.py").symlink_to(outside)
    subprocess.run(["git", "-C", str(peer), "add", "main.py"], check=True)
    subprocess.run(["git", "-C", str(peer), "commit", "-m", "symlink"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(peer), "push"], check=True, capture_output=True)
    old_head = gitstore.head_short(settings, project["id"])
    response = client.post("/api/play/pull?base_revision=1", headers=auth(token))
    assert response.status_code == 502 and "Links" in response.text
    assert gitstore.head_short(settings, project["id"]) == old_head
    _save(client, token, "safe = 'still safe'\n")
    assert outside.read_text() == "unchanged"


def test_existing_symlink_cannot_be_written_during_save(client, teacher_csrf, settings, tmp_path):
    project = create_project(client, teacher_csrf)[0]
    token = student_token(client, project["code"])
    _save(client, token, "before = 1\n")
    outside = tmp_path / "outside.py"
    outside.write_text("unchanged")
    source = gitstore.repo_dir(settings, project["id"]) / "main.py"
    source.unlink()
    source.symlink_to(outside)
    response = _save(client, token, "after = 2\n")
    assert "Links" in response["warning"]
    assert outside.read_text() == "unchanged"
    assert client.get("/api/play/project", headers=auth(token)).json()["save"]["source"] == "after = 2\n"


def test_save_and_git_commit_are_serialized_for_the_same_project(client, teacher_csrf, settings, monkeypatch):
    project = create_project(client, teacher_csrf)[0]
    token = student_token(client, project["code"])
    first_entered, release_first, second_entered = threading.Event(), threading.Event(), threading.Event()
    original = gitstore.commit_save
    def delayed(settings, project_id, source, *args, **kwargs):
        if source == "first = 1\n":
            first_entered.set()
            assert release_first.wait(5)
        else:
            second_entered.set()
        return original(settings, project_id, source, *args, **kwargs)
    monkeypatch.setattr(gitstore, "commit_save", delayed)
    responses = []
    def save(source, revision):
        responses.append(client.put("/api/play/save", json={"source": source, "base_revision": revision}, headers=auth(token)))
    first = threading.Thread(target=save, args=("first = 1\n", 0))
    second = threading.Thread(target=save, args=("second = 2\n", 1))
    first.start()
    try:
        assert first_entered.wait(3)
        second.start()
        assert not second_entered.wait(0.2)
    finally:
        release_first.set()
        first.join(5)
        if second.ident:
            second.join(5)
    assert len(responses) == 2 and all(r.status_code == 200 for r in responses)
    assert json.loads(gitstore.read_save_at(settings, project["id"], "HEAD"))["source"] == "second = 2\n"


def test_media_quota_is_serialized_across_server_processes(client, teacher_csrf, settings, monkeypatch):
    import app.routes.play_api as play
    project = create_project(client, teacher_csrf)[0]
    token = student_token(client, project["code"])
    second_app = create_app(settings, enable_yearly_task=False)
    first_entered, release_first, second_entered = threading.Event(), threading.Event(), threading.Event()
    original = play.compute_used_bytes
    call_lock = threading.Lock()
    calls = 0
    def delayed(*args, **kwargs):
        nonlocal calls
        with call_lock:
            calls += 1
            number = calls
        used = original(*args, **kwargs)
        if number == 1:
            first_entered.set()
            assert release_first.wait(5)
        else:
            second_entered.set()
        return used
    monkeypatch.setattr(play, "compute_used_bytes", delayed)
    content = b"\x89PNG\r\n\x1a\n" + bytes(6 * 1024 * 1024)
    responses = []
    def upload(http, name):
        responses.append(http.post("/api/play/media", headers=auth(token), files={"file": (name, io.BytesIO(content), "image/png")}))
    with TestClient(second_app) as other:
        first = threading.Thread(target=upload, args=(client, "one.png"))
        second = threading.Thread(target=upload, args=(other, "two.png"))
        first.start()
        try:
            assert first_entered.wait(3)
            second.start()
            assert not second_entered.wait(0.2)
        finally:
            release_first.set()
            first.join(5)
            if second.ident:
                second.join(5)
    second_app.state.engine.dispose()
    assert sorted(r.status_code for r in responses) == [200, 413]
