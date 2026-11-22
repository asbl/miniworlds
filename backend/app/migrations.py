"""Idempotente Schema- und Datenschutzmigrationen für SQLite-Installationen."""
import json
import zlib

from sqlalchemy import inspect, text

from .task_data import checkbox_answers, clean_snapshot, information_items


def remove_text_answers(conn):
    conn.execute(text("UPDATE task_items SET kind='text' WHERE kind='textarea'"))
    for vid, payload, snapshot in conn.execute(text("SELECT id, payload, project_snapshot FROM submission_versions")):
        cleaned = json.dumps(checkbox_answers(json.loads(payload))).encode()
        frozen = snapshot
        if snapshot is not None:
            # Read the raw snapshot here so the migration actually rewrites removed types.
            original = json.loads(zlib.decompress(snapshot))
            sanitized = clean_snapshot(original)
            if sanitized != original:
                frozen = zlib.compress(json.dumps(sanitized, ensure_ascii=False).encode())
        if json.loads(payload) != json.loads(cleaned) or frozen != snapshot:
            conn.execute(text("UPDATE submission_versions SET payload=:payload, project_snapshot=:snapshot WHERE id=:id"),
                         {"payload": cleaned, "snapshot": frozen, "id": vid})
    for pid, payload in conn.execute(text("SELECT id, items FROM public_tasks")):
        original = json.loads(payload)
        cleaned = information_items(original)
        if cleaned != original:
            conn.execute(text("UPDATE public_tasks SET items=:items WHERE id=:id"),
                         {"items": json.dumps(cleaned, ensure_ascii=False).encode(), "id": pid})


def migrate(engine) -> None:
    additions = {
        "audit_log": {"teacher_id": "INTEGER REFERENCES users(id) ON DELETE CASCADE"},
        "projects": {
            "workspace_id": "INTEGER REFERENCES workspaces(id) ON DELETE SET NULL",
            "course_id": "INTEGER REFERENCES courses(id) ON DELETE SET NULL",
            "title": "VARCHAR(120) NOT NULL DEFAULT 'Mein Projekt'",
            "revision": "INTEGER NOT NULL DEFAULT 0",
        },
        "tasks": {
            "source_public_task_id": "INTEGER REFERENCES public_tasks(id) ON DELETE SET NULL",
            "course_id": "INTEGER REFERENCES courses(id) ON DELETE SET NULL",
        },
        "submission_versions": {"project_snapshot": "BLOB"},
    }
    with engine.begin() as conn:
        for column in ("teacher_note", "feedback", "reviewed_at"):
            if column in {c["name"] for c in inspect(conn).get_columns("submissions")}:
                conn.execute(text(f"ALTER TABLE submissions DROP COLUMN {column}"))
        # Alte Notizen auch aus dem Audit entfernen; keine Rückmeldungen aufbewahren.
        for aid, meta in conn.execute(text("SELECT id, meta FROM audit_log WHERE meta IS NOT NULL")).all():
            data = json.loads(meta) if isinstance(meta, str) else meta
            if isinstance(data, dict) and any(k in data for k in ("teacher_note", "feedback")):
                for key in ("teacher_note", "feedback"):
                    data.pop(key, None)
                conn.execute(text("UPDATE audit_log SET meta=:meta WHERE id=:id"), {"meta": json.dumps(data), "id": aid})
        for table, columns in additions.items():
            existing = {c["name"] for c in inspect(conn).get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        # Bestehende Codes erhalten jeweils einen eigenen, namenlosen Arbeitsbereich.
        for pid, teacher_id in conn.execute(text("SELECT id, teacher_id FROM projects WHERE workspace_id IS NULL")).all():
            result = conn.execute(text("INSERT INTO workspaces (teacher_id) VALUES (:teacher)"), {"teacher": teacher_id})
            conn.execute(text("UPDATE projects SET workspace_id=:workspace WHERE id=:pid"), {"workspace": result.lastrowid, "pid": pid})
        for table, column in (("projects", "course_id"), ("projects", "workspace_id"), ("tasks", "course_id"), ("audit_log", "teacher_id")):
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})"))
        if conn.execute(text("SELECT value FROM settings WHERE key='technical_audit_v1'")).scalar() != "1":
            from .audit import audit_meta
            users = {email: (uid, role) for uid, email, role in conn.execute(text("SELECT id, email, role FROM users"))}
            users_by_id = {uid: role for uid, role in users.values()}
            owners = dict(conn.execute(text("SELECT id, teacher_id FROM projects")).all())
            for aid, kind, ref, target, meta in conn.execute(text("SELECT id, actor_type, actor_ref, target, meta FROM audit_log")).all():
                ref, target = ref or "", target or ""
                owner = None
                if ref in users:
                    uid, role = users[ref]
                    ref = f"user:{uid}"
                    owner = uid if role == "teacher" else None
                elif ref.startswith("user:") and ref.split(":", 1)[1].isdecimal():
                    uid = int(ref.split(":", 1)[1])
                    owner = uid if users_by_id.get(uid) == "teacher" else None
                elif kind == "code" and ref.startswith("project:"):
                    owner = owners.get(int(ref.split(":", 1)[1]))
                elif kind == "system" and target.startswith("project:"):
                    owner = owners.get(int(target.split(":", 1)[1]))
                    ref = ""
                else:
                    ref = ""
                data = json.loads(meta) if isinstance(meta, str) else meta
                if "://" in target or target.startswith("git@"):
                    target = ref if ref.startswith("project:") else ""
                conn.execute(text("UPDATE audit_log SET actor_ref=:ref, teacher_id=:owner, target=:target, meta=:meta WHERE id=:id"),
                             {"ref": ref, "owner": owner, "target": target, "meta": json.dumps(audit_meta(data)), "id": aid})
            conn.execute(text("INSERT OR REPLACE INTO settings (key, value) VALUES ('technical_audit_v1', '1')"))
        if conn.execute(text("SELECT value FROM settings WHERE key='checkbox_only_v1'")).scalar() != "1":
            remove_text_answers(conn)
            conn.execute(text("INSERT OR REPLACE INTO settings (key, value) VALUES ('checkbox_only_v1', '1')"))
