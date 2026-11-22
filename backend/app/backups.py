"""Konsistente SQLite-Sicherungen mit obligatorischer Wiederherstellungsprüfung.

Aufruf im backend-Verzeichnis: python -m app.backups --help
Der Schlüssel kommt ausschließlich aus SECRET_KEY, niemals aus dem Archiv.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import uuid
import zipfile

from sqlalchemy.engine import make_url

from .config import load_settings
from .locking import storage_lock
from .models import utcnow
from .security import decrypt_code, decrypt_secret, encryption_key_check


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _signature(manifest, secret):
    return hmac.new(secret.encode(), _canonical(manifest), hashlib.sha256).hexdigest()


def _safe_path(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or any(p in {"", ".", ".."} for p in name.split("/")):
        raise ValueError("Unsicherer Dateipfad im Sicherungsarchiv.")
    if name != "app.db" and (len(path.parts) < 2 or path.parts[0] not in {"media", "git"}):
        raise ValueError("Unbekannter Dateibereich im Sicherungsarchiv.")
    return path


def _file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_restored(root, secret):
    db = sqlite3.connect(f"{(root / 'app.db').as_uri()}?mode=ro", uri=True)
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Datenbankprüfung der Sicherung fehlgeschlagen.")
        check = db.execute("SELECT value FROM settings WHERE key='encryption_key_check'").fetchone()
        if check and not hmac.compare_digest(check[0], encryption_key_check(secret)):
            raise ValueError("SECRET_KEY passt nicht zur gesicherten Datenbank.")
        for (code,) in db.execute("SELECT code_enc FROM projects"):
            decrypt_code(code, secret)
        for (token,) in db.execute("SELECT token_enc FROM project_remotes WHERE token_enc IS NOT NULL"):
            decrypt_secret(token, secret)
        for pid, stored, size, checksum in db.execute("SELECT project_id, stored_name, size_bytes, sha256 FROM media_assets"):
            name = f"media/{pid}/{stored}"
            _safe_path(name)
            path = root / name
            if not path.is_file() or path.stat().st_size != size or (checksum and _file_digest(path) != checksum):
                raise ValueError("Eine Mediendatei fehlt oder ist beschädigt.")
        for sid, payload in db.execute("SELECT id, payload FROM snapshots"):
            for asset in json.loads(payload).get("media", []):
                name = f"media/snapshots/{sid}/{asset['stored_name']}"
                _safe_path(name)
                if not (root / name).is_file() or (root / name).stat().st_size != asset["size_bytes"]:
                    raise ValueError("Eine veröffentlichte Mediendatei fehlt oder ist beschädigt.")
        from .archives import unpack_snapshot
        for (payload,) in db.execute("SELECT project_snapshot FROM submission_versions WHERE project_snapshot IS NOT NULL"):
            unpack_snapshot(payload)
        project_count = db.execute("SELECT count(*) FROM projects").fetchone()[0]
    finally:
        db.close()
    repos = list((root / "git").glob("project-*/.git"))
    if repos and not shutil.which("git"):
        raise ValueError("Git wird für die Wiederherstellungsprüfung benötigt.")
    for repo in repos:
        result = subprocess.run(["git", "-C", str(repo.parent), "fsck", "--full"], capture_output=True, timeout=120)
        if result.returncode:
            raise ValueError("Ein Git-Verlauf ist beschädigt.")
    return {"projects": project_count, "git_repositories": len(repos)}


def _unpack_verified(archive_path, destination, secret):
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "manifest.json" not in names:
            raise ValueError("Ungültiges Sicherungsarchiv.")
        document = json.loads(archive.read("manifest.json"))
        manifest, signature = document["manifest"], document["signature"]
        if manifest.get("format") != 1 or not hmac.compare_digest(signature, _signature(manifest, secret)):
            raise ValueError("Sicherung oder SECRET_KEY stimmen nicht; Signaturprüfung fehlgeschlagen.")
        if set(names) != set(manifest["files"]) | {"manifest.json"} or "app.db" not in manifest["files"]:
            raise ValueError("Die Dateiliste der Sicherung stimmt nicht.")
        for name, expected in manifest["files"].items():
            _safe_path(name)
            info = archive.getinfo(name)
            if stat.S_ISLNK(info.external_attr >> 16) or info.file_size != expected["size"]:
                raise ValueError("Unsicherer oder beschädigter Archiveintrag.")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
            os.chmod(target, 0o600)
            if _file_digest(target) != expected["sha256"]:
                raise ValueError("Prüfsumme einer Sicherungsdatei stimmt nicht.")
    (destination / "media").mkdir(exist_ok=True)
    (destination / "git").mkdir(exist_ok=True)
    return _check_restored(destination, secret)


def verify_backup(archive_path, secret):
    with tempfile.TemporaryDirectory(prefix="miniworlds-restore-check-") as directory:
        return _unpack_verified(Path(archive_path), Path(directory), secret)


def restore_backup(archive_path, destination, secret):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("Das Wiederherstellungsziel muss neu sein; vorhandene Daten werden nicht überschrieben.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".miniworlds-restore-", dir=destination.parent) as directory:
        staged = Path(directory) / "restored"
        staged.mkdir(mode=0o700)
        result = _unpack_verified(Path(archive_path), staged, secret)
        staged.rename(destination)
    return result


def create_backup(settings, directory, *, keep=7):
    settings.validate()
    if keep < 1:
        raise ValueError("Mindestens eine Sicherung muss aufbewahrt werden.")
    db_url = make_url(settings.database_url)
    if db_url.get_backend_name() != "sqlite" or not db_url.database or db_url.database == ":memory:":
        raise ValueError("Diese Sicherung benötigt eine dateibasierte SQLite-Datenbank.")
    database = Path(db_url.database).resolve()
    if not database.is_file():
        raise ValueError("Die Backend-Datenbank existiert noch nicht.")
    directory = Path(directory).resolve()
    for root in (Path(settings.media_root).resolve(), Path(settings.git_root).resolve()):
        if directory == root or root in directory.parents:
            raise ValueError("Sicherungen müssen außerhalb der Medien- und Git-Verzeichnisse liegen.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = f"miniworlds-{utcnow():%Y%m%dT%H%M%S}-{uuid.uuid4().hex}.zip"
    target = directory / name
    with tempfile.TemporaryDirectory(prefix=".backup-", dir=directory) as temporary:
        temporary = Path(temporary)
        output = temporary / name
        with storage_lock(settings, exclusive=True):
            db_copy = temporary / "app.db"
            with sqlite3.connect(database) as source, sqlite3.connect(db_copy) as dest:
                source.backup(dest)
            files = {"app.db": db_copy}
            for prefix, root in (("media", Path(settings.media_root)), ("git", Path(settings.git_root))):
                for path in root.rglob("*"):
                    if path.is_symlink():
                        raise ValueError("Sicherungen dürfen keine symbolischen Links enthalten.")
                    if not path.is_file() or (path.parent == root and path.name.startswith(".") and path.name.endswith(".lock")):
                        continue
                    files[f"{prefix}/{path.relative_to(root).as_posix()}"] = path
            manifest = {"format": 1, "created_at": utcnow().isoformat(), "files": {}}
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                os.chmod(output, 0o600)
                for member, path in sorted(files.items()):
                    _safe_path(member)
                    manifest["files"][member] = {"size": path.stat().st_size, "sha256": _file_digest(path)}
                    archive.write(path, member)
                archive.writestr("manifest.json", _canonical({"manifest": manifest, "signature": _signature(manifest, settings.secret_key)}))
        # Jede neue Sicherung wird vollständig wiederhergestellt und geprüft.
        verify_backup(output, settings.secret_key)
        output.rename(target)
    managed = re.compile(r"miniworlds-\d{8}T\d{6}-[0-9a-f]{32}\.zip")
    previous = sorted((p for p in directory.iterdir() if managed.fullmatch(p.name)), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    for old in previous[keep:]:
        old.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Sichern, Wiederherstellung prüfen und alte Sicherungen begrenzen")
    create.add_argument("--directory", required=True)
    create.add_argument("--keep", type=int, default=7)
    verify = commands.add_parser("verify", help="Eine Sicherung vollständig probeweise wiederherstellen")
    verify.add_argument("archive")
    restore = commands.add_parser("restore", help="In ein neues Verzeichnis wiederherstellen")
    restore.add_argument("archive")
    restore.add_argument("--destination", required=True)
    args = parser.parse_args()
    try:
        settings = load_settings()
        if args.command == "create":
            print(create_backup(settings, args.directory, keep=args.keep))
        elif args.command == "verify":
            print(json.dumps({"ok": True, **verify_backup(args.archive, settings.secret_key)}))
        else:
            print(json.dumps({"ok": True, **restore_backup(args.archive, args.destination, settings.secret_key)}))
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, f"Sicherung fehlgeschlagen: {error}\n")


if __name__ == "__main__":
    main()
