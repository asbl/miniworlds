from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_GIT_HOSTS = "github.com,gitlab.com,codeberg.org"


@dataclass
class Settings:
    secret_key: str = ""  # dauerhaft setzen; wird auch zur Verschlüsselung verwendet
    database_url: str = "sqlite:///./data/app.db"
    media_root: str = "./data/media"
    git_root: str = "./data/git"  # server-seitige git-Repos pro Projekt (Versionsverlauf)
    git_allowed_hosts: str = DEFAULT_GIT_HOSTS  # exakte Hosts; "local" erlaubt Dateipfade nur in Tests
    admin_email: str | None = None
    admin_password: str | None = None
    base_url: str = "http://localhost:8000"
    session_hours: int = 12
    student_token_hours: int = 12
    invite_expire_days: int = 30
    default_quota_bytes: int = 10 * 1024 * 1024
    teacher_quota_cap: int = 50 * 1024 * 1024
    cookie_secure: bool = False  # in Produktion hinter HTTPS auf True setzen
    miniworlds_wheel_path: str = ""  # leer = app/static/wheel/miniworlds.whl
    pyodide_base: str = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/"
    retention_read_only_months: int = 24
    retention_delete_months: int = 36
    audit_retention_days: int = 30
    history_max_bytes: int = 100 * 1024 * 1024
    submission_max_versions: int = 10
    submission_max_bytes: int = 100 * 1024 * 1024
    max_request_bytes: int = 64 * 1024 * 1024
    frontend_origins: str = "https://editor.opencoding.de"
    code_readonly_days: int = 365

    def validate(self) -> None:
        if self.code_readonly_days < 1:
            raise ValueError("CODE_READONLY_DAYS muss mindestens 1 sein.")
        if not self.secret_key.strip():
            raise ValueError("SECRET_KEY fehlt. Einen dauerhaften Schlüssel konfigurieren und mit den Sicherungen aufbewahren.")
        for name in ("audit_retention_days", "history_max_bytes", "submission_max_versions", "submission_max_bytes", "max_request_bytes"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} muss größer als null sein.")
        if self.history_max_bytes < 64 * 1024:
            raise ValueError("HISTORY_MAX_BYTES muss mindestens 65536 Bytes betragen (Git-Verwaltungsdaten).")


def load_settings() -> Settings:
    secret = os.environ.get("SECRET_KEY")
    settings = Settings(
        secret_key=secret or "",
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./data/app.db"),
        media_root=os.environ.get("MEDIA_ROOT", "./data/media"),
        git_root=os.environ.get("MINIWORLDS_GIT_ROOT", "./data/git"),
        git_allowed_hosts=os.environ.get("GIT_ALLOWED_HOSTS", DEFAULT_GIT_HOSTS),
        admin_email=os.environ.get("ADMIN_EMAIL") or None,
        admin_password=os.environ.get("ADMIN_PASSWORD") or None,
        base_url=os.environ.get("BASE_URL", "http://localhost:8000"),
        session_hours=int(os.environ.get("SESSION_HOURS", "12")),
        student_token_hours=int(os.environ.get("STUDENT_TOKEN_HOURS", "12")),
        invite_expire_days=int(os.environ.get("INVITE_EXPIRE_DAYS", "30")),
        default_quota_bytes=int(os.environ.get("DEFAULT_QUOTA_BYTES", str(10 * 1024 * 1024))),
        teacher_quota_cap=int(os.environ.get("TEACHER_QUOTA_CAP", str(50 * 1024 * 1024))),
        cookie_secure=os.environ.get("COOKIE_SECURE", "0") == "1",
        miniworlds_wheel_path=os.environ.get(
            "MINIWORLDS_WHEEL_PATH",
            str(__import__("pathlib").Path(__file__).parent / "static" / "wheel" / "miniworlds.whl"),
        ),
        pyodide_base=os.environ.get("PYODIDE_BASE", "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/"),
        retention_read_only_months=int(os.environ.get("RETENTION_READ_ONLY_MONTHS", "24")),
        retention_delete_months=int(os.environ.get("RETENTION_DELETE_MONTHS", "36")),
        audit_retention_days=int(os.environ.get("AUDIT_RETENTION_DAYS", "30")),
        history_max_bytes=int(os.environ.get("HISTORY_MAX_BYTES", str(100 * 1024 * 1024))),
        submission_max_versions=int(os.environ.get("SUBMISSION_MAX_VERSIONS", "10")),
        submission_max_bytes=int(os.environ.get("SUBMISSION_MAX_BYTES", str(100 * 1024 * 1024))),
        max_request_bytes=int(os.environ.get("MAX_REQUEST_BYTES", str(64 * 1024 * 1024))),
        frontend_origins=os.environ.get("FRONTEND_ORIGINS", "https://editor.opencoding.de"),
        code_readonly_days=int(os.environ.get("CODE_READONLY_DAYS", "365")),
    )
    settings.validate()
    return settings
