import base64
import io
import json
import threading
import zipfile
from datetime import timedelta

from fastapi.testclient import TestClient

from app.models import Project, Course, TemplateCode, Workspace, utcnow, aware
from app.projects import code_expiry
from app.yearly import maybe_yearly_reset
from .conftest import auth, create_project, student_token, make_teacher


def patch(client, csrf, pid, **values):
    result = client.patch(f"/api/teacher/projects/{pid}", headers={"X-CSRF-Token": csrf}, json=values)
    assert result.status_code == 200, result.text
    return result.json()


def test_expiry_blocks_new_claim_and_existing_token(client, app, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    patch(client, teacher_csrf, p['id'], code_expires_at=(utcnow()-timedelta(seconds=1)).isoformat())
    assert client.post('/api/claim', json={'code': p['code']}).status_code == 401
    assert client.get('/api/play/project', headers=auth(token)).status_code == 401
    patch(client, teacher_csrf, p['id'], code_expires_at=None)
    assert client.get('/api/play/project', headers=auth(token)).status_code == 200


def test_readonly_default_and_configured_expiry(client, app, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    patch(client, teacher_csrf, p['id'], read_only=True)
    with app.state.SessionLocal() as db:
        row = db.get(Project, p['id'])
        started = aware(row.read_only_at)
        assert code_expiry(db, row) == started + timedelta(days=365)
    patch(client, teacher_csrf, p['id'], code_readonly_days=20)
    with app.state.SessionLocal() as db:
        assert code_expiry(db, db.get(Project, p['id'])) == started + timedelta(days=20)
    # Repeated locks and annual maintenance must never extend an existing deadline.
    patch(client, teacher_csrf, p['id'], read_only=True)
    with app.state.SessionLocal() as db:
        maybe_yearly_reset(db, now=utcnow()+timedelta(days=400))
        assert aware(db.get(Project, p['id']).read_only_at) == started
    patch(client, teacher_csrf, p['id'], code_readonly_days=None)
    with app.state.SessionLocal() as db:
        assert code_expiry(db, db.get(Project, p['id'])) is None


def test_scheduled_readonly_and_no_deadline_bypass(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    patch(client, teacher_csrf, p['id'], writable_until=(utcnow()-timedelta(days=2)).isoformat(), code_readonly_days=3)
    project = client.get('/api/play/project', headers=auth(token)).json()
    assert project['read_only'] and project['code_expires_at']
    assert client.put('/api/play/save', headers=auth(token), json={'source': 'x'}).status_code == 403
    patch(client, teacher_csrf, p['id'], code_readonly_days=1)
    assert client.get('/api/play/project', headers=auth(token)).status_code == 401


def test_deadlines_roundtrip_with_timezone(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    result = patch(client, teacher_csrf, p['id'], writable_until='2028-07-31T15:00:00+02:00', code_expires_at='2029-07-31T15:00:00+02:00')
    assert result['project']['writable_until'] == '2028-07-31T13:00:00+00:00'
    assert result['project']['code_expires_at'] == '2029-07-31T13:00:00+00:00'


def test_archiving_starts_and_reactivation_removes_archive_deadline(client, teacher_csrf):
    headers = {'X-CSRF-Token': teacher_csrf}
    cid = client.post('/api/teacher/courses', headers=headers, json={'title': '7a'}).json()['id']
    p = client.post('/api/teacher/projects', headers=headers, json={'course_id': cid}).json()['projects'][0]
    client.patch(f'/api/teacher/courses/{cid}', headers=headers, json={'archived': True})
    row = client.get('/api/teacher/projects', headers=headers).json()['projects'][0]
    assert row['read_only'] and row['effective_code_expires_at']
    client.patch(f'/api/teacher/courses/{cid}', headers=headers, json={'archived': False})
    row = client.get('/api/teacher/projects', headers=headers).json()['projects'][0]
    assert not row['read_only'] and row['effective_code_expires_at'] is None


def test_password_invalidates_all_workspace_sessions_and_teacher_can_reset(client, app, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    sibling = client.post('/api/play/projects', headers=auth(token), json={'title': 'Zweites'}).json()
    password = 'lange sichere passphrase'
    protected = client.put('/api/play/password', headers=auth(token), json={'password': password})
    assert protected.status_code == 200, protected.text
    fresh = protected.json()['token']
    assert client.get('/api/play/project', headers=auth(token)).status_code == 401
    assert client.get('/api/play/project', headers=auth(sibling['token'])).status_code == 401
    assert client.get('/api/play/project', headers=auth(fresh)).json()['password_protected']
    assert client.post('/api/claim', json={'code': p['code']}).status_code == 401
    assert client.post('/api/claim', json={'code': p['code'], 'password': password}).status_code == 200
    assert client.put('/api/play/password', headers=auth(fresh), json={'password': 'andere lange passphrase', 'current_password': 'falsch'}).status_code == 401
    assert client.delete(f"/api/teacher/projects/{p['id']}/password", headers={'X-CSRF-Token': teacher_csrf}).status_code == 200
    assert client.get('/api/play/project', headers=auth(fresh)).status_code == 401
    assert client.post('/api/claim', json={'code': p['code']}).status_code == 200
    with app.state.SessionLocal() as db:
        assert db.get(Workspace, db.get(Project, p['id']).workspace_id).password_hash is None


def test_password_attempt_limit_survives_app_restart(client, app, settings, teacher_csrf):
    from app.main import create_app
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    client.put('/api/play/password', headers=auth(token), json={'password': 'ein sicheres langes Passwort'})
    for _ in range(5):
        assert client.post('/api/claim', json={'code': p['code'], 'password': 'falsch'}).status_code == 401
    with TestClient(create_app(settings, enable_yearly_task=False)) as other:
        assert other.post('/api/claim', json={'code': p['code'], 'password': 'ein sicheres langes Passwort'}).status_code == 429


def test_template_code_is_atomic_and_copies_without_access_to_original(client, app, teacher_csrf):
    source = create_project(client, teacher_csrf)[0]
    token = student_token(client, source['code'])
    client.put('/api/play/save', headers=auth(token), json={'source': 'print("Vorlage")'})
    result = client.post('/api/teacher/projects', headers={'X-CSRF-Token': teacher_csrf}, json={'access_mode': 'template_once', 'template_project_id': source['id']})
    code = result.json()['projects'][0]['code']
    results = []
    def redeem():
        with TestClient(app) as c:
            results.append(c.post('/api/claim', json={'code': code}))
    threads = [threading.Thread(target=redeem) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sorted(r.status_code for r in results) == [200, 401]
    created = next(r.json() for r in results if r.status_code == 200)
    assert created['personal_code'] != source['code'] and created['project_id'] != source['id']
    project = client.get('/api/play/project', headers=auth(created['token'])).json()
    assert project['save']['source'] == 'print("Vorlage")'
    assert len(client.get('/api/play/projects', headers=auth(created['token'])).json()['projects']) == 1
    assert student_token(client, created['personal_code'])
    with app.state.SessionLocal() as db:
        assert db.query(Project).count() == 2 and db.query(TemplateCode).one().used_at


def test_expired_or_revoked_template_does_not_create_project(client, app, teacher_csrf):
    source = create_project(client, teacher_csrf)[0]
    result = client.post('/api/teacher/projects', headers={'X-CSRF-Token': teacher_csrf}, json={'access_mode': 'template_once', 'template_project_id': source['id'], 'code_expires_at': (utcnow()-timedelta(seconds=1)).isoformat()}).json()
    assert client.post('/api/claim', json={'code': result['projects'][0]['code']}).status_code == 401
    with app.state.SessionLocal() as db:
        assert db.query(Project).count() == 1


def test_editor_files_survive_history_export_and_legacy_saves(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    b64 = lambda value: base64.b64encode(value).decode()
    files = {'main.py': b64(b'from classes.actor import x\n'), 'classes/actor.py': b64(b'x=7\n'), 'images/test.bin': b64(bytes(range(256)))}
    result = client.put('/api/play/save', headers=auth(token), json={'source': 'from classes.actor import x\n', 'files': files})
    assert result.status_code == 200, result.text
    first = result.json()
    assert client.get('/api/play/project', headers=auth(token)).json()['save']['files'] == files
    result = client.put('/api/play/save', headers=auth(token), json={'source': 'print(8)\n', 'base_revision': first['revision']})
    assert result.status_code == 200
    saved = client.get('/api/play/project', headers=auth(token)).json()['save']['files']
    assert saved['classes/actor.py'] == files['classes/actor.py'] and saved['main.py'] == b64(b'print(8)\n')
    restored = client.post(f"/api/play/restore/{first['commit']}?base_revision={result.json()['revision']}", headers=auth(token))
    assert restored.status_code == 200, restored.text
    assert restored.json()['save']['files'] == files
    archive = zipfile.ZipFile(io.BytesIO(client.get('/api/play/download', headers=auth(token)).content))
    assert archive.read('classes/actor.py') == b'x=7\n' and archive.read('images/test.bin') == bytes(range(256))


def test_unsafe_paths_rejected_without_saving(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    for path in ('../outside', '/absolute', '.git/config', 'foo\\bar', 'foo//bar', 'main.py/other'):
        files = {path: '', 'main.py': ''}
        response = client.put('/api/play/save', headers=auth(token), json={'source': 'x', 'files': files})
        assert response.status_code == 422, (path, response.text)
    assert client.get('/api/play/project', headers=auth(token)).json()['save'] is None


def test_editor_media_changes_and_legacy_uploads_stay_consistent(client, teacher_csrf):
    from .test_media import PNG, _upload
    p = create_project(client, teacher_csrf)[0]
    token = student_token(client, p['code'])
    first = _upload(client, token, PNG, 'a.png').json()['media']
    files = {'a.png': base64.b64encode(PNG+b'changed').decode()}
    result = client.put('/api/play/save', headers=auth(token), json={'source': 'x=1', 'files': files})
    assert result.status_code == 200, result.text
    assert client.get(f"/api/play/media/{first['id']}/file", headers=auth(token)).content == PNG+b'changed'
    second = _upload(client, token, PNG, 'b.png')
    assert second.status_code == 200, second.text
    saved = client.get('/api/play/project', headers=auth(token)).json()
    assert 'b.png' in saved['save']['files']
    files = saved['save']['files']
    del files['a.png']
    result = client.put('/api/play/save', headers=auth(token), json={'source': 'x=1', 'files': files, 'base_revision': saved['revision']})
    assert result.status_code == 200, result.text
    assert client.get(f"/api/play/media/{first['id']}/file", headers=auth(token)).status_code == 404
    assert [a['orig_name'] for a in client.get('/api/play/media', headers=auth(token)).json()['media']] == ['b.png']


def test_cors_exact_origin_preflight_and_errors(client, teacher_csrf):
    headers = {'Origin': 'https://editor.opencoding.de', 'Access-Control-Request-Method': 'PUT', 'Access-Control-Request-Headers': 'authorization,content-type'}
    response = client.options('/api/play/save', headers=headers)
    assert response.status_code == 200 and response.headers['Access-Control-Allow-Origin'] == headers['Origin']
    assert 'Access-Control-Allow-Credentials' not in response.headers
    headers['Origin'] = 'https://evil.example'
    assert client.options('/api/play/save', headers=headers).status_code == 400
    response = client.get('/api/play/project', headers={'Origin': 'https://editor.opencoding.de'})
    assert response.status_code == 401 and response.headers['Access-Control-Allow-Origin'] == 'https://editor.opencoding.de'
    response = client.put('/api/play/save', content=b'{}', headers={'Origin': 'https://editor.opencoding.de', 'Content-Length': str(100*1024*1024)})
    assert response.status_code == 413 and response.headers['Access-Control-Allow-Origin'] == 'https://editor.opencoding.de'


def test_other_teacher_cannot_change_access_or_reset_password(client, teacher_csrf):
    p = create_project(client, teacher_csrf)[0]
    other = make_teacher(client, email='other@schule.de')
    headers = {'X-CSRF-Token': other}
    assert client.patch(f"/api/teacher/projects/{p['id']}", headers=headers, json={'code_expires_at': None}).status_code == 404
    assert client.delete(f"/api/teacher/projects/{p['id']}/password", headers=headers).status_code == 404
