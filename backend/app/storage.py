"""Begrenzte Aufbewahrung eingefrorener Abgaben pro Projekt."""
from fastapi import HTTPException

from .models import Submission, SubmissionVersion


def submission_bytes(db, project_id):
    return sum(len(v.payload) + len(v.project_snapshot or b"") for v in
               db.query(SubmissionVersion).join(Submission).filter(Submission.project_id == project_id))


def limit_submissions(db, settings, project_id, *, enforce=True):
    rows = (db.query(SubmissionVersion).join(Submission)
            .filter(Submission.project_id == project_id).order_by(SubmissionVersion.id.desc()).all())
    counts, protected, remove = {}, set(), []
    total = 0
    for row in rows:
        if row.submitted:
            counts[row.submission_id] = counts.get(row.submission_id, 0) + 1
            if counts[row.submission_id] == 1:
                protected.add(row.id)
            if counts[row.submission_id] > settings.submission_max_versions:
                remove.append(row)
                continue
        else:
            sub = db.get(Submission, row.submission_id)
            if row.version != sub.current_version:
                remove.append(row)
                continue
            protected.add(row.id)
        total += len(row.payload) + len(row.project_snapshot or b"")
    # Bei vollem Gesamtbudget zuerst alte Fassungen entfernen, die aktuelle
    # Abgabe jeder Aufgabe bleibt immer erhalten.
    for row in reversed(rows):
        if total <= settings.submission_max_bytes:
            break
        if row.id in protected or row in remove:
            continue
        total -= len(row.payload) + len(row.project_snapshot or b"")
        remove.append(row)
    if enforce and total > settings.submission_max_bytes:
        raise HTTPException(413, "Der Archivspeicher ist voll. Diese Abgabe wurde nicht gespeichert. Bitte das Projekt verkleinern oder die Lehrkraft informieren.")
    for row in remove:
        db.delete(row)
    db.flush()
    return total


def storage_policy(settings):
    return {"history_max_bytes": settings.history_max_bytes,
            "submission_max_versions": settings.submission_max_versions,
            "submission_max_bytes": settings.submission_max_bytes}
