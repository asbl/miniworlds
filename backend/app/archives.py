"""Portable Projektarchive und unveränderliche Abgaben ohne Personen-/Feedbackfelder."""
import base64
import binascii
import io
import json
import re
import zipfile
import zlib

from fastapi import HTTPException

from .models import MediaAsset, Save, utcnow
from .services import project_media_dir
from .task_data import checkbox_answers, clean_snapshot


def pack_snapshot(data):
    return zlib.compress(json.dumps(clean_snapshot(data), ensure_ascii=False).encode())


def unpack_snapshot(payload):
    return clean_snapshot(json.loads(zlib.decompress(payload)))


def media_name(asset_id, original):
    # Ein Name für Player, Archive und Quellcode; Kollisionen werden beim Upload verhindert.
    name = re.sub(r"[^\w.\-]", "_", original, flags=re.ASCII).strip(".")
    return name if name and name not in {"main.py", "save.db", "project.json", "licenses.json"} else f"asset-{asset_id}"


def project_snapshot(db, settings, p, task=None):
    save = db.get(Save, p.id)
    data = {"format": 1, "project_id": p.id, "title": p.title, "revision": p.revision,
            "frozen_at": utcnow().isoformat(), "save": json.loads(save.payload) if save else None, "media": []}
    if task:
        data["task"] = {"id": task.id, "title": task.title, "description": task.description,
                        "items": [{"id": i.id, "kind": i.kind, "prompt": i.prompt, "position": i.position}
                                  for i in sorted(task.items, key=lambda i: i.position)]}
    for a in db.query(MediaAsset).filter_by(project_id=p.id).order_by(MediaAsset.id):
        path = project_media_dir(settings, p.id) / a.stored_name
        if not path.is_file():
            raise HTTPException(409, f"Die Mediendatei {a.orig_name} fehlt. Bitte erneut hochladen.")
        data["media"].append({"id": a.id, "orig_name": a.orig_name, "filename": media_name(a.id, a.orig_name),
                              "mime": a.mime, "license": a.license, "license_text": a.license_text,
                              "source": a.source, "content": base64.b64encode(path.read_bytes()).decode()})
    return data


def project_zip(data, answers=None):
    data = clean_snapshot(data)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        save = data.get("save") or {}
        archive.writestr("main.py", save.get("source", ""))
        if save.get("db"):
            try:
                db_bytes = base64.b64decode(save["db"], validate=True)
            except (ValueError, binascii.Error):
                db_bytes = save["db"].encode()
            archive.writestr("save.db", db_bytes)
        licenses = []
        for asset in data.get("media", []):
            archive.writestr(asset["filename"], base64.b64decode(asset["content"]))
            licenses.append({k: asset[k] for k in ("filename", "license", "license_text", "source")})
        archive.writestr("licenses.json", json.dumps(licenses, ensure_ascii=False, indent=2))
        manifest = {k: v for k, v in data.items() if k not in ("save", "media")}
        if answers is not None:
            manifest["answers"] = checkbox_answers(answers)
        archive.writestr("project.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return buf.getvalue()
