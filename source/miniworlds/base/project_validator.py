"""
Project structure validator for miniworlds projects.

Each issue carries two severities:
- ``local_severity``: relevance when running on the local desktop
- ``web_severity``: relevance when targeting the Pyodide/browser export

Example::

    from pathlib import Path
    from miniworlds.base.project_validator import ProjectValidator, Severity

    issues = ProjectValidator(project_dir, entry_file).validate()
    web_errors = [i for i in issues if i.web_severity == Severity.ERROR]
"""

from __future__ import annotations

import ast
import mimetypes
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(Enum):
    NONE = 0     # not an issue in this context
    INFO = 1
    WARNING = 2
    ERROR = 3


class IssueCode(Enum):
    SYNTAX_ERROR = "syntax_error"
    ENCODING_ERROR = "encoding_error"
    ENTRY_NOT_MAIN = "entry_not_main"
    PROBLEMATIC_IMPORT = "problematic_import"
    NO_MINIWORLDS_IMPORT = "no_miniworlds_import"
    FILE_WRITE_IO = "file_write_io"
    ABSOLUTE_PATH = "absolute_path"
    LARGE_ASSET = "large_asset"
    LARGE_TOTAL_ASSETS = "large_total_assets"
    UNSUPPORTED_IMAGE_FORMAT = "unsupported_image_format"
    UNSUPPORTED_SOUND_FORMAT = "unsupported_sound_format"


@dataclass
class ValidationIssue:
    code: IssueCode
    message: str
    local_severity: Severity
    web_severity: Severity


# (local_severity, web_severity, human-readable description)
_PROBLEMATIC_IMPORTS: dict[str, tuple[Severity, Severity, str]] = {
    "tkinter":         (Severity.NONE, Severity.ERROR,   "tkinter ist im Browser nicht verfügbar."),
    "_tkinter":        (Severity.NONE, Severity.ERROR,   "tkinter ist im Browser nicht verfügbar."),
    "subprocess":      (Severity.NONE, Severity.ERROR,   "subprocess ist im Browser nicht verfügbar."),
    "multiprocessing": (Severity.NONE, Severity.ERROR,   "multiprocessing ist im Browser nicht verfügbar."),
    "ctypes":          (Severity.NONE, Severity.ERROR,   "ctypes ist im Browser nicht verfügbar."),
    "socket":          (Severity.NONE, Severity.WARNING, "socket hat im Browser eingeschränkte Funktion."),
    "requests":        (Severity.NONE, Severity.ERROR,   "requests ist im Browser nicht verfügbar."),
    "urllib":          (Severity.NONE, Severity.WARNING, "urllib ist im Browser eingeschränkt verfügbar."),
    "http":            (Severity.NONE, Severity.WARNING, "http ist im Browser eingeschränkt verfügbar."),
    "ftplib":          (Severity.NONE, Severity.ERROR,   "ftplib ist im Browser nicht verfügbar."),
    "smtplib":         (Severity.NONE, Severity.ERROR,   "smtplib ist im Browser nicht verfügbar."),
    "sqlite3":         (Severity.NONE, Severity.ERROR,   "sqlite3 ist im Browser nicht verfügbar."),
    "PyQt5":           (Severity.NONE, Severity.ERROR,   "PyQt5 ist im Browser nicht verfügbar."),
    "PyQt6":           (Severity.NONE, Severity.ERROR,   "PyQt6 ist im Browser nicht verfügbar."),
    "PySide2":         (Severity.NONE, Severity.ERROR,   "PySide2 ist im Browser nicht verfügbar."),
    "PySide6":         (Severity.NONE, Severity.ERROR,   "PySide6 ist im Browser nicht verfügbar."),
    "wx":              (Severity.NONE, Severity.ERROR,   "wx (wxPython) ist im Browser nicht verfügbar."),
}

_SUPPORTED_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"})
_SUPPORTED_SOUND_EXTS = frozenset({".wav", ".ogg", ".mp3"})

_ASSET_FILE_WARN_BYTES = 2 * 1024 * 1024   # 2 MB per file
_TOTAL_SIZE_WARN_BYTES = 25 * 1024 * 1024  # 25 MB total

_RE_WRITE_OPEN = re.compile(r"""open\s*\(.*?["'](w|a|x|wb|ab|xb)["']""")
_RE_ABS_PATH = re.compile(r"""["'](/(?:[^/\s"'][^"']*))["']|["']([A-Za-z]:\\[^"']+)["']""")


def _mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def _collect_assets(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    return [
        {
            "path": f"{folder.name}/{f.name}",
            "name": f.name,
            "mimeType": _mime(f),
            "size": f.stat().st_size,
        }
        for f in sorted(folder.iterdir())
        if f.is_file() and not f.name.startswith(".")
    ]


class ProjectValidator:
    """Validates a miniworlds project directory for common local and web issues."""

    def __init__(self, project_dir: Path, entry_file: Path) -> None:
        self.project_dir = Path(project_dir)
        self.entry_file = Path(entry_file)

    def validate(self) -> list[ValidationIssue]:
        py_files = sorted(
            f for f in self.project_dir.glob("*.py") if not f.name.startswith(".")
        )
        images = _collect_assets(self.project_dir / "images")
        sounds = _collect_assets(self.project_dir / "sounds")

        issues: list[ValidationIssue] = []
        issues += self._check_syntax(py_files)
        issues += self._check_entry_name()
        issues += self._check_problematic_imports(py_files)
        issues += self._check_miniworlds_import(py_files)
        issues += self._check_file_io(py_files)
        issues += self._check_asset_sizes(images, sounds)
        issues += self._check_asset_formats(images, sounds)
        return issues

    # ------------------------------------------------------------------

    def _check_syntax(self, py_files: list[Path]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for f in py_files:
            try:
                source = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                issues.append(ValidationIssue(
                    code=IssueCode.ENCODING_ERROR,
                    message=f"{f.name}: Datei ist nicht UTF-8-kodiert.",
                    local_severity=Severity.ERROR,
                    web_severity=Severity.ERROR,
                ))
                continue
            try:
                ast.parse(source, filename=f.name)
            except SyntaxError as exc:
                issues.append(ValidationIssue(
                    code=IssueCode.SYNTAX_ERROR,
                    message=f"{f.name}: Syntaxfehler in Zeile {exc.lineno} – {exc.msg}",
                    local_severity=Severity.ERROR,
                    web_severity=Severity.ERROR,
                ))
        return issues

    def _check_entry_name(self) -> list[ValidationIssue]:
        if self.entry_file.name != "main.py":
            return [ValidationIssue(
                code=IssueCode.ENTRY_NOT_MAIN,
                message=(
                    f'Die Einstiegsdatei heißt „{self.entry_file.name}" statt „main.py". '
                    "Der Webplayer erwartet main.py als Startdatei."
                ),
                local_severity=Severity.NONE,
                web_severity=Severity.WARNING,
            )]
        return []

    def _check_problematic_imports(self, py_files: list[Path]) -> list[ValidationIssue]:
        seen: set[tuple[str, str]] = set()
        issues: list[ValidationIssue] = []
        for f in py_files:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=f.name)
            except Exception:
                continue  # syntax errors reported elsewhere
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    tops = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    tops = [node.module.split(".")[0]] if node.module else []
                else:
                    continue
                for top in tops:
                    if top in _PROBLEMATIC_IMPORTS:
                        key = (f.name, top)
                        if key not in seen:
                            seen.add(key)
                            local_sev, web_sev, desc = _PROBLEMATIC_IMPORTS[top]
                            issues.append(ValidationIssue(
                                code=IssueCode.PROBLEMATIC_IMPORT,
                                message=f"{f.name}: {desc}",
                                local_severity=local_sev,
                                web_severity=web_sev,
                            ))
        return issues

    def _check_miniworlds_import(self, py_files: list[Path]) -> list[ValidationIssue]:
        for f in py_files:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=f.name)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(a.name.startswith("miniworlds") for a in node.names):
                        return []
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("miniworlds"):
                        return []
        return [ValidationIssue(
            code=IssueCode.NO_MINIWORLDS_IMPORT,
            message="Kein miniworlds-Import gefunden – ist das wirklich ein miniworlds-Projekt?",
            local_severity=Severity.INFO,
            web_severity=Severity.WARNING,
        )]

    def _check_file_io(self, py_files: list[Path]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for f in py_files:
            try:
                source = f.read_text(encoding="utf-8")
            except Exception:
                continue
            if _RE_WRITE_OPEN.search(source):
                issues.append(ValidationIssue(
                    code=IssueCode.FILE_WRITE_IO,
                    message=(
                        f"{f.name}: open() mit Schreibmodus ('w'/'a') – "
                        "Datei-Schreibzugriffe sind im Browser nicht persistent."
                    ),
                    local_severity=Severity.NONE,
                    web_severity=Severity.WARNING,
                ))
            m = _RE_ABS_PATH.search(source)
            if m:
                path_str = (m.group(1) or m.group(2))[:50]
                issues.append(ValidationIssue(
                    code=IssueCode.ABSOLUTE_PATH,
                    message=(
                        f'{f.name}: Absoluter Dateipfad gefunden ("{path_str}") – '
                        "absolute Pfade funktionieren im Browser nicht."
                    ),
                    local_severity=Severity.NONE,
                    web_severity=Severity.ERROR,
                ))
        return issues

    def _check_asset_sizes(
        self, images: list[dict], sounds: list[dict]
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for info in images + sounds:
            if info["size"] > _ASSET_FILE_WARN_BYTES:
                mb = info["size"] / (1024 * 1024)
                issues.append(ValidationIssue(
                    code=IssueCode.LARGE_ASSET,
                    message=(
                        f"Asset „{info['name']}“ ist {mb:.1f} MB groß – "
                        "große Dateien verlangsamen das Laden im Browser."
                    ),
                    local_severity=Severity.INFO,
                    web_severity=Severity.WARNING,
                ))
        total = sum(info["size"] for info in images + sounds)
        if total > _TOTAL_SIZE_WARN_BYTES:
            issues.append(ValidationIssue(
                code=IssueCode.LARGE_TOTAL_ASSETS,
                message=(
                    f"Gesamtgröße der Assets beträgt {total / (1024 * 1024):.1f} MB – "
                    "das kann das Laden im Browser stark verlangsamen."
                ),
                local_severity=Severity.INFO,
                web_severity=Severity.WARNING,
            ))
        return issues

    def _check_asset_formats(
        self, images: list[dict], sounds: list[dict]
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for info in images:
            ext = Path(info["name"]).suffix.lower()
            if ext not in _SUPPORTED_IMAGE_EXTS:
                issues.append(ValidationIssue(
                    code=IssueCode.UNSUPPORTED_IMAGE_FORMAT,
                    message=(
                        f'Bilddatei „{info["name"]}“: Format „{ext}“ wird im Browser '
                        f"möglicherweise nicht unterstützt "
                        f"(empfohlen: {', '.join(sorted(_SUPPORTED_IMAGE_EXTS))})."
                    ),
                    local_severity=Severity.INFO,
                    web_severity=Severity.WARNING,
                ))
        for info in sounds:
            ext = Path(info["name"]).suffix.lower()
            if ext not in _SUPPORTED_SOUND_EXTS:
                issues.append(ValidationIssue(
                    code=IssueCode.UNSUPPORTED_SOUND_FORMAT,
                    message=(
                        f'Sounddatei „{info["name"]}“: Format „{ext}“ wird im Browser '
                        f"möglicherweise nicht unterstützt "
                        f"(empfohlen: {', '.join(sorted(_SUPPORTED_SOUND_EXTS))})."
                    ),
                    local_severity=Severity.INFO,
                    web_severity=Severity.WARNING,
                ))
        return issues
