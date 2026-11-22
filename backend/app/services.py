from __future__ import annotations

import json
import shutil
from datetime import timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from .config import Settings
from .models import MediaAsset, Project, Save, Snapshot, Submission, SubmissionVersion, TaskAssignment, utcnow
from .security import decrypt_code
from .task_data import checkbox_answers
from .yearly import get_setting

# Erlaubte Medientypen: Endung -> (MIME, Magic-Bytes-Prüfung)
ALLOWED_MEDIA: dict[str, tuple[str, bytes | None, int]] = {
    # (mime, magic prefix or None, offset)
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n", 0),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff", 0),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff", 0),
    ".gif": ("image/gif", b"GIF8", 0),
    ".webp": ("image/webp", b"RIFF", 0),  # + WEBP an Offset 8
    ".mp3": ("audio/mpeg", None, 0),  # ID3 oder Frame-Sync
    ".ogg": ("audio/ogg", b"OggS", 0),
    ".wav": ("audio/wav", b"RIFF", 0),
    ".mp4": ("video/mp4", b"ftyp", 4),
    ".webm": ("video/webm", b"\x1a\x45\xdf\xa3", 0),
}
MAX_MEDIA_FILE_BYTES = 25 * 1024 * 1024  # hartes Limit pro Datei

LICENSE_CHOICES = ["eigene Erstellung", "CC0", "CC-BY", "CC-BY-SA", "CC-BY-NC", "GPL/andere OSS", "andere (Freitext)"]


def compute_used_bytes(db: Session, project: Project) -> int:
    """Quota-Verbrauch: Save + Medien + aktuelle Abgabe-Versionen des Projekts."""
    total = 0
    save = db.get(Save, project.id)
    if save:
        total += save.size_bytes
    total += sum(r[0] or 0 for r in db.query(MediaAsset.size_bytes).filter_by(project_id=project.id).all())
    subs = db.query(Submission).filter_by(project_id=project.id).all()
    for sub in subs:
        v = (
            db.query(SubmissionVersion)
            .filter_by(submission_id=sub.id)
            .order_by(SubmissionVersion.version.desc())
            .first()
        )
        if v:
            total += len(v.payload)
    return total


def serialize_project(db: Session, p: Project, settings: Settings | None = None, with_code: bool = False) -> dict:
    from .projects import read_only_reason
    d = {
        "id": p.id,
        "title": p.title,
        "course_id": p.course_id,
        "workspace_id": p.workspace_id,
        "revision": p.revision,
        "quota_bytes": p.quota_bytes,
        "used_bytes": compute_used_bytes(db, p),
        "read_only": bool(read_only_reason(db, p)),
        "manual_read_only": p.read_only,
        "read_only_reason": read_only_reason(db, p),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "last_save_at": p.last_save_at.isoformat() if p.last_save_at else None,
        "tasks_assigned": db.query(TaskAssignment).filter_by(project_id=p.id).count(),
    }
    if with_code and settings is not None:
        d["code"] = decrypt_code(p.code_enc, settings.secret_key)
    return d


def latest_version(db: Session, submission: Submission) -> SubmissionVersion | None:
    if not submission.current_version:
        return None
    return (
        db.query(SubmissionVersion)
        .filter_by(submission_id=submission.id, version=submission.current_version)
        .first()
    )


def decode_answers(db: Session, submission: Submission | None) -> dict:
    if not submission:
        return {}
    v = latest_version(db, submission)
    if not v:
        return {}
    return checkbox_answers(json.loads(v.payload))


def default_quota(db: Session, settings: Settings) -> int:
    return int(get_setting(db, "student_default_quota", str(settings.default_quota_bytes)) or settings.default_quota_bytes)


def quota_cap(db: Session, settings: Settings) -> int:
    return int(get_setting(db, "teacher_quota_cap", str(settings.teacher_quota_cap)) or settings.teacher_quota_cap)


def project_media_dir(settings: Settings, project_id: int) -> Path:
    return Path(settings.media_root) / str(project_id)


def snapshot_media_dir(settings: Settings, snapshot_id: int) -> Path:
    return Path(settings.media_root) / "snapshots" / str(snapshot_id)


def cleanup_orphan_snapshots(db, settings):
    """Alte Reste früherer Löschungen bereinigen; unter exklusiver Speichersperre."""
    root = Path(settings.media_root) / "snapshots"
    if not root.is_dir():
        return
    retained = {str(sid) for (sid,) in db.query(Snapshot.id)}
    cutoff = (utcnow() - timedelta(days=1)).timestamp()
    for directory in root.iterdir():
        if directory.name.isdecimal() and directory.name not in retained and directory.is_dir() and directory.stat().st_mtime < cutoff:
            shutil.rmtree(directory)


def delete_project_files(settings: Settings, project_id: int) -> None:
    path = project_media_dir(settings, project_id)
    if path.exists():
        shutil.rmtree(path)


def delete_project_cascade(db: Session, settings: Settings, p: Project) -> None:
    """Löscht ein Projekt inkl. Abgaben, Save, Medien (DB + Dateien)."""
    from .models import MediaAsset, Snapshot, TaskAssignment

    # Öffentliche Kopien liegen außerhalb des Projektordners und werden nicht
    # durch die Datenbank-Cascade oder delete_project_files entfernt.
    for (snapshot_id,) in db.query(Snapshot.id).filter_by(project_id=p.id):
        path = snapshot_media_dir(settings, snapshot_id)
        if path.exists():
            shutil.rmtree(path)

    for a in db.query(TaskAssignment).filter_by(project_id=p.id).all():
        for sub in db.query(Submission).filter_by(assignment_id=a.id).all():
            db.query(SubmissionVersion).filter_by(submission_id=sub.id).delete()
            db.delete(sub)
        db.delete(a)
    db.query(Save).filter_by(project_id=p.id).delete()
    db.query(MediaAsset).filter_by(project_id=p.id).delete()
    delete_project_files(settings, p.id)
    from .gitstore import delete_repo

    delete_repo(settings, p.id)
    db.delete(p)


def check_media_head(head: bytes, ext: str) -> bool:
    """Magic-Bytes-Prüfung anhand des Datei-Anfangs."""
    spec = ALLOWED_MEDIA.get(ext)
    if not spec:
        return False
    _mime, magic, offset = spec
    if magic is None:
        # mp3: ID3-Tag oder Frame-Sync (0xFF 0xFB/0xF3/0xF2)
        return head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] in (0xFB, 0xF3, 0xF2))
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if ext == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    return head[offset : offset + len(magic)] == magic
