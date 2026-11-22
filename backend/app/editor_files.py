"""Validiertes, portables Dateiformat des optionalen statischen Editors."""
import base64
import binascii
import re

from fastapi import HTTPException

MANIFEST = ".miniworlds-editor-files.json"


def valid_path(path):
    return (isinstance(path, str) and 0 < len(path) <= 240 and
            not path.startswith("/") and not re.search(r"[\\:\x00-\x1f\x7f]", path) and
            all(part not in {"", ".", "..", ".git", MANIFEST} for part in path.split("/")))


def validate_files(files):
    if not isinstance(files, dict) or len(files) > 2000:
        raise HTTPException(422, "Ungültige Projektdateien (höchstens 2000 Dateien).")
    paths = set(files)
    for path, content in files.items():
        if not valid_path(path) or not isinstance(content, str):
            raise HTTPException(422, "Ungültiger Projektpfad oder Dateiinhalt.")
        if any("/".join(path.split("/")[:n]) in paths for n in range(1, len(path.split("/")))):
            raise HTTPException(422, "Eine Datei kann nicht gleichzeitig ein Ordner sein.")
        try:
            base64.b64decode(content, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(422, "Projektdatei ist kein gültiges Base64.") from None
    return files


def save_payload(source, database, files=None):
    result = {"source": source, "db": database}
    if files is not None:
        files = dict(validate_files(files))
        if "main.py" in files or source:
            files["main.py"] = base64.b64encode(source.encode()).decode()
        if database:
            files["save.db"] = database
        else:
            files.pop("save.db", None)
        result["files"] = validate_files(files)
    return result
