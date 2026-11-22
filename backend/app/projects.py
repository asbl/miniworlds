"""Gemeinsame Regeln für Arbeitsstände, Klassen und Code-Arbeitsbereiche."""
from fastapi import HTTPException
from sqlalchemy import or_, update

from .models import Course, Project, Save, Submission, Task, TaskAssignment, Workspace, utcnow
from .security import encrypt_code, gen_code, hash_code
from .services import compute_used_bytes, default_quota


def owned_course(db, teacher_id, cid):
    course = db.get(Course, cid) if cid is not None else None
    if cid is not None and (not course or course.teacher_id != teacher_id):
        raise HTTPException(404, "Klasse nicht gefunden")
    return course


def read_only_reason(db, p):
    course = db.get(Course, p.course_id) if p.course_id else None
    if course and course.archived:
        return "Die Klasse ist archiviert. Die Lehrkraft kann sie wieder aktivieren."
    if p.read_only:
        return "Das Projekt ist schreibgeschützt. Ansehen und Herunterladen bleiben möglich."
    return None


def require_writable(db, p):
    reason = read_only_reason(db, p)
    if reason:
        raise HTTPException(403, reason)


def assign_templates(db, p):
    tasks = db.query(Task).filter(
        Task.teacher_id == p.teacher_id, Task.is_template_for_new_projects.is_(True),
        or_(Task.course_id.is_(None), Task.course_id == p.course_id),
    ).all()
    for task in tasks:
        if db.query(TaskAssignment).filter_by(task_id=task.id, project_id=p.id).first():
            continue
        a = TaskAssignment(task_id=task.id, project_id=p.id)
        db.add(a)
        db.flush()
        db.add(Submission(assignment_id=a.id, project_id=p.id))


def new_project(db, settings, teacher_id, course_id=None, workspace_id=None, title="Mein Projekt"):
    course = owned_course(db, teacher_id, course_id)
    if course and course.archived:
        raise HTTPException(409, "In einer archivierten Klasse können keine Projekte angelegt werden")
    if workspace_id is None:
        workspace = Workspace(teacher_id=teacher_id)
        db.add(workspace)
        db.flush()
        workspace_id = workspace.id
    code = gen_code(10)
    p = Project(teacher_id=teacher_id, workspace_id=workspace_id, course_id=course_id,
                title=title, revision=0, code_hash=hash_code(code),
                code_enc=encrypt_code(code, settings.secret_key), quota_bytes=default_quota(db, settings))
    db.add(p)
    db.flush()
    assign_templates(db, p)
    return p, code


def copy_project_content(db, settings, p, snapshot):
    """Nur Programm und Medien kopieren, niemals Antworten, Freigaben oder Tokens."""
    import base64
    import hashlib
    import json
    from pathlib import Path
    from .models import MediaAsset
    from .services import project_media_dir

    if snapshot.get("save") is not None:
        payload = json.dumps(snapshot["save"]).encode()
        db.add(Save(project_id=p.id, payload=payload, size_bytes=len(payload)))
        p.revision = 1
        p.last_save_at = utcnow()
    for asset in snapshot["media"]:
        content = base64.b64decode(asset["content"])
        row = MediaAsset(project_id=p.id, orig_name=asset["orig_name"], mime=asset["mime"],
                         size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                         license=asset["license"], license_text=asset["license_text"], source=asset["source"])
        db.add(row)
        db.flush()
        row.stored_name = f"{row.id}{Path(asset['orig_name']).suffix.lower()}"
        directory = project_media_dir(settings, p.id)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / row.stored_name).write_bytes(content)
    db.flush()


def store_save(db, p, payload, base_revision):
    """Compare-and-swap: auch gleichzeitige Requests dürfen keinen Stand überschreiben."""
    require_writable(db, p)
    if base_revision is None:
        raise HTTPException(428, "Bitte den aktuellen Projektstand laden, bevor du speicherst")
    old = db.get(Save, p.id)
    used = compute_used_bytes(db, p) - (old.size_bytes if old else 0) + len(payload)
    if used > p.quota_bytes:
        raise HTTPException(413, "Speicherplatz voll. Lade dein Projekt herunter oder entferne nicht mehr benötigte Medien.")
    result = db.execute(update(Project).where(Project.id == p.id, Project.revision == base_revision)
                        .values(revision=Project.revision + 1, last_save_at=utcnow())
                        .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "In einem anderen Tab wurde ein neuerer Stand gespeichert. Dein Entwurf bleibt lokal erhalten.")
    if old:
        old.payload, old.size_bytes, old.updated_at = payload, len(payload), utcnow()
    else:
        db.add(Save(project_id=p.id, payload=payload, size_bytes=len(payload)))
    db.flush()
    db.refresh(p)
    return p.revision
