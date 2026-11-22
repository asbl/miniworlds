"""Server-seitige git-Repositories pro Schülerprojekt.

Jedes Projekt erhält unter ``settings.git_root`` ein eigenes git-Repository
(Arbeitsbaum mit ``main.py``, ``save.db`` und ``media/``). Jeder Speichervorgang
im Player erzeugt einen Commit — das ist die git-Integration für Schüler:
Verlauf ansehen, Diff anzeigen, alte Version wiederherstellen.

Das Modul hängt nur von der Config ab und kapselt alle subprocess-Aufrufe.
"""

from __future__ import annotations

import base64
import contextlib
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import fcntl
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .config import DEFAULT_GIT_HOSTS, Settings

AUTHOR = "miniworlds server"
EMAIL = "server@miniworlds.local"

_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


class GitError(Exception):
    """git-Vorgang fehlgeschlagen; die Message ist deutsch und für Schüler geeignet."""


def git_available() -> bool:
    return shutil.which("git") is not None


def repo_dir(settings: Settings, project_id: int) -> Path:
    return Path(settings.git_root) / f"project-{project_id}"


def locked_project(function):
    @wraps(function)
    def run(settings, project_id, *args, **kwargs):
        root = Path(settings.git_root)
        root.mkdir(parents=True, exist_ok=True)
        # Außerhalb des Repos, damit Löschen den Lock nicht ungültig macht.
        with (root / f".project-{project_id}.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return function(settings, project_id, *args, **kwargs)
    return run


def history_bytes(settings: Settings, project_id: int) -> int:
    directory = repo_dir(settings, project_id) / ".git"
    total = 0
    for path in directory.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass  # eine parallele git gc kann lose Objekte gerade ersetzen
    return total


def history_paused(settings: Settings, project_id: int) -> bool:
    return (repo_dir(settings, project_id) / ".history-full").exists()


@locked_project
def history_bundle(settings: Settings, project_id: int) -> bytes:
    repo = _require_repo(settings, project_id)
    with tempfile.TemporaryDirectory(prefix="mw-history-") as directory:
        target = Path(directory) / "history.bundle"
        _checked(repo, "bundle", "create", str(target), "HEAD")
        return target.read_bytes()


@locked_project
def delete_repo(settings: Settings, project_id: int) -> None:
    path = repo_dir(settings, project_id)
    if path.exists():
        shutil.rmtree(path)


def _git(repo: Path, *args: str, timeout: int = 30, env: dict | None = None) -> subprocess.CompletedProcess:
    if not repo.is_dir():
        raise GitError("Repository existiert noch nicht")
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        raise GitError("git ist auf dem Server nicht installiert") from None
    except subprocess.TimeoutExpired:
        raise GitError(f"git {' '.join(args[:2])} wurde nach {timeout}s abgebrochen") from None


def _checked(repo: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    result = _git(repo, *args, timeout=timeout)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(err[:300] if err else f"git {args[0]} ist fehlgeschlagen")
    return result


def _out(result: subprocess.CompletedProcess) -> str:
    return result.stdout.decode("utf-8", "replace")


def _ensure_identity(repo: Path) -> None:
    if not _out(_git(repo, "config", "user.email")).strip():
        _checked(repo, "config", "user.name", AUTHOR)
        _checked(repo, "config", "user.email", EMAIL)


def ensure_repo(settings: Settings, project_id: int) -> Path:
    repo = repo_dir(settings, project_id)
    if not (repo / ".git").exists():
        repo.mkdir(parents=True, exist_ok=True)
        _checked(repo, "init")
        _ensure_identity(repo)
    return repo


def _sync_media(repo: Path, media_src: Path) -> None:
    dst = repo / "media"
    names = {f.name for f in media_src.iterdir() if f.is_file()} if media_src.is_dir() else set()
    if names:
        dst.mkdir(exist_ok=True)
        for name in names:
            shutil.copy2(media_src / name, dst / name)
    if dst.is_dir():
        for f in dst.iterdir():
            if f.is_file() and f.name not in names:
                f.unlink()


def _check_worktree(repo: Path) -> None:
    # Ein Remote kann main.py, save.db oder media als Link auschecken. Kein
    # anschließender Schreib-/Kopiervorgang darf solchen Links folgen.
    if repo.is_symlink() or any(path.is_symlink() for path in repo.rglob("*")):
        raise GitError("Symbolische Links sind in Projekt-Repositories nicht erlaubt.")


def _check_remote_tree(repo: Path) -> None:
    for entry in _checked(repo, "ls-tree", "-rz", "HEAD").stdout.split(b"\0"):
        if entry and entry.split(b" ", 1)[0] not in {b"100644", b"100755"}:
            raise GitError("Symbolische Links und Submodule sind in Projekt-Repositories nicht erlaubt.")
    _check_worktree(repo)


def _commit_if_dirty(repo: Path, message: str, settings: Settings, project_id: int) -> str | None:
    if history_paused(settings, project_id):
        raise GitError("Der Versionsverlauf ist voll und pausiert. Dein aktuelles Projekt ist gespeichert. Lade den Verlauf herunter oder lösche ihn, um neue Versionen anzulegen.")
    old_head = _git(repo, "rev-parse", "--verify", "HEAD")
    _checked(repo, "add", "-A")
    if _git(repo, "diff", "--cached", "--quiet").returncode == 0:
        return None  # keine Änderungen seit dem letzten Commit
    _checked(repo, "commit", "-m", message)
    if history_bytes(settings, project_id) > settings.history_max_bytes:
        # Verdichten, bevor das Budget als voll gilt. Einen zu großen neuen
        # Commit wieder entfernen; der aktuelle Arbeitsstand bleibt in der DB.
        _checked(repo, "gc", "--prune=now")
        if history_bytes(settings, project_id) > settings.history_max_bytes:
            if old_head.returncode == 0:
                _checked(repo, "reset", "--mixed", _out(old_head).strip())
            else:
                ref = _out(_checked(repo, "symbolic-ref", "HEAD")).strip()
                _checked(repo, "update-ref", "-d", ref)
                _checked(repo, "read-tree", "--empty")
            _checked(repo, "reflog", "expire", "--expire=now", "--all")
            _checked(repo, "gc", "--prune=now")
            (repo / ".history-full").touch()
            raise GitError("Der Versionsverlauf ist voll und pausiert. Dein aktuelles Projekt ist gespeichert. Vorhandene Versionen kannst du weiterhin herunterladen.")
    return _out(_checked(repo, "rev-parse", "--short", "HEAD")).strip()


@locked_project
def commit_save(
    settings: Settings,
    project_id: int,
    source: str,
    db_bytes: bytes | None,
    message: str,
) -> str | None:
    """Schreibt main.py/save.db/media ins Repo und committet. None bei leerem Commit."""
    if not git_available():
        return None
    repo = ensure_repo(settings, project_id)
    _check_worktree(repo)
    (repo / "main.py").write_text(source, encoding="utf-8")
    db_file = repo / "save.db"
    if db_bytes is None:
        db_file.unlink(missing_ok=True)
    else:
        db_file.write_bytes(db_bytes)
    _sync_media(repo, Path(settings.media_root) / str(project_id))
    return _commit_if_dirty(repo, message.strip() or "Speichern", settings, project_id)


@locked_project
def commit_media(settings: Settings, project_id: int, message: str) -> str | None:
    """Nur die Medien ins Repo übernehmen und committen (Upload/Löschen)."""
    if not git_available():
        return None
    repo = ensure_repo(settings, project_id)
    _check_worktree(repo)
    _sync_media(repo, Path(settings.media_root) / str(project_id))
    return _commit_if_dirty(repo, message.strip() or "Medien aktualisiert", settings, project_id)


def _require_repo(settings: Settings, project_id: int) -> Path:
    repo = repo_dir(settings, project_id)
    if not (repo / ".git").exists():
        raise GitError("Für dieses Projekt gibt es noch keinen Versionsverlauf")
    return repo


def history(settings: Settings, project_id: int, limit: int = 50) -> list[dict]:
    """Commits, neueste zuerst: [{hash, short, date, message}]."""
    repo = repo_dir(settings, project_id)
    if not (repo / ".git").exists():
        return []
    result = _git(repo, "log", f"--max-count={int(limit)}", "--pretty=format:%H%x00%h%x00%ad%x00%s", "--date=iso-strict")
    if result.returncode != 0:
        return []
    commits = []
    for line in _out(result).splitlines():
        parts = line.split("\0")
        if len(parts) == 4:
            commits.append({"hash": parts[0], "short": parts[1], "date": parts[2], "message": parts[3]})
    return commits


def _check_commit(commit: str) -> str:
    commit = (commit or "").strip().lower()
    if commit == "head":
        return "HEAD"
    if not _COMMIT_RE.match(commit):
        raise GitError(f"Ungültiger Commit-Bezeichner: {commit!r}")
    return commit


def show(settings: Settings, project_id: int, commit: str) -> str:
    """Commit-Metadaten + Diff als Text."""
    repo = _require_repo(settings, project_id)
    return _out(_checked(repo, "show", "--date=iso-strict", _check_commit(commit)))


def read_save_at(settings: Settings, project_id: int, commit: str) -> bytes:
    """Save-Payload (JSON: source + base64-db) aus einem Commit rekonstruieren."""
    repo = _require_repo(settings, project_id)
    commit = _check_commit(commit)
    source = _out(_checked(repo, "show", f"{commit}:main.py"))
    db_result = _git(repo, "show", f"{commit}:save.db")
    db_b64 = base64.b64encode(db_result.stdout).decode() if db_result.returncode == 0 and db_result.stdout else None
    return json.dumps({"source": source, "db": db_b64}).encode()


# ---------- Remotes (Push/Pull, z. B. GitHub) ----------


def _is_private_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host in {"localhost", "0.0.0.0", "::1"} or host.endswith(".local") or host.endswith(".internal"):
        return True
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        return not ip.is_global
    except ValueError:
        return False


def validate_remote_url(url: str, allowed_hosts: str = DEFAULT_GIT_HOSTS) -> str:
    """Remote-Adresse prüfen: nur https/ssh (ggf. Host-Whitelist), keine Credentials in der URL.

    Das Literal „local“ in allowed_hosts erlaubt Datei-Pfade (nur für Tests).
    """
    url = (url or "").strip()
    if not url or len(url) > 500 or any(ord(c) < 32 or c.isspace() for c in url):
        raise GitError("Ungültige Remote-Adresse.")
    allowed = {h.strip().lower().rstrip(".") for h in (allowed_hosts or "").split(",") if h.strip()}
    allow_local = "local" in allowed
    if allow_local and (url.startswith("/") or url.startswith("file://")):
        return url
    if url.startswith("git@"):
        match = re.fullmatch(r"git@([A-Za-z0-9.-]+):(.+)", url)
        if not match:
            raise GitError("Ungültige SSH-Remote-Adresse.")
        host = match.group(1).lower().rstrip(".")
        _check_remote_host(host, allowed)
        return f"git@{host}:{match.group(2)}"
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise GitError("Ungültige Remote-Adresse.") from None
    if parsed.scheme != "https" or not parsed.hostname or not parsed.path or parsed.query or parsed.fragment:
        raise GitError("Nur https://- oder git@…-Adressen sind erlaubt, z. B. https://github.com/user/repo.git")
    if parsed.username is not None or parsed.password is not None:
        raise GitError("Zugangsdaten dürfen nicht in der URL stehen — das Token wird getrennt gespeichert.")
    host = parsed.hostname.lower().rstrip(".")
    if port not in (None, 443):
        raise GitError("HTTPS-Remotes müssen Port 443 verwenden.")
    _check_remote_host(host, allowed)
    authority = f"[{host}]" if ":" in host else host
    return urlunsplit(("https", authority, parsed.path, "", ""))


def _check_remote_host(host: str, allowed: set[str]) -> None:
    if _is_private_host(host):
        raise GitError("Interne/lokale Adressen sind als Remote nicht erlaubt.")
    if host not in allowed or host == "local":
        raise GitError(f"Host „{host}“ ist nicht in der Whitelist (erlaubt: {', '.join(sorted(allowed))}).")
    try:
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise GitError("Der Git-Host kann nicht aufgelöst werden. Bitte Netzwerk und Adresse prüfen.") from None
    if not addresses or any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
        raise GitError("Interne/lokale Adressen sind als Remote nicht erlaubt.")


def remote_url(settings: Settings, project_id: int) -> str | None:
    repo = repo_dir(settings, project_id)
    if not (repo / ".git").exists():
        return None
    result = _git(repo, "remote", "get-url", "origin")
    return _out(result).strip() if result.returncode == 0 else None


@locked_project
def set_remote(settings: Settings, project_id: int, url: str) -> None:
    repo = ensure_repo(settings, project_id)
    _git(repo, "remote", "remove", "origin")  # älteren Remote ersetzen (Fehler egal)
    _checked(repo, "remote", "add", "origin", url)


@locked_project
def remove_remote(settings: Settings, project_id: int) -> None:
    repo = repo_dir(settings, project_id)
    if (repo / ".git").exists():
        _git(repo, "remote", "remove", "origin")


@contextlib.contextmanager
def _askpass(token: str | None):
    """Token per GIT_ASKPASS injizieren — landet nie in argv oder .git/config."""
    if not token:
        yield {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        return
    with tempfile.TemporaryDirectory(prefix="mw-askpass-") as tmp:
        script = Path(tmp) / "askpass.sh"
        script.write_text(
            "#!/bin/sh\n"
            'case "$1" in\n'
            '  *sername*|*Username*) echo "${MW_GIT_USER:-x-access-token}" ;;\n'
            '  *) echo "$MW_GIT_TOKEN" ;;\n'
            "esac\n",
            encoding="utf-8",
        )
        script.chmod(0o700)
        yield {
            **os.environ,
            "GIT_ASKPASS": str(script),
            "GIT_TERMINAL_PROMPT": "0",
            "MW_GIT_TOKEN": token,
        }


def _remote_error(op: str, stderr: str) -> str:
    text = (stderr or "").lower()
    if any(k in text for k in ("authentication failed", "could not read username", "permission denied", "access denied", "authorization failed", "403")):
        return "Zugriff verweigert — Token und Remote-Adresse prüfen (GitHub: PAT mit repo-Recht)."
    if "non-fast-forward" in text or "rejected" in text or "fetch first" in text:
        return "Das Remote hat neuere Versionen — zuerst „Pull“ ausführen."
    if "not found" in text or "404" in text or "does not appear to be a git repository" in text:
        return "Remote-Repository nicht gefunden — URL prüfen (Groß-/Kleinschreibung, .git-Endung)."
    if "timed out" in text or "could not resolve host" in text or "connection" in text:
        return "Remote ist nicht erreichbar — Netzwerk und URL prüfen."
    return f"git {op} ist fehlgeschlagen: {stderr.strip()[:200]}"


def _current_branch(repo: Path) -> str:
    branch = _out(_git(repo, "branch", "--show-current")).strip()
    if not branch:
        raise GitError("Das Repository hat keinen Branch — zuerst einmal speichern.")
    return branch


@locked_project
def push(settings: Settings, project_id: int, token: str | None) -> str:
    """Aktuellen Branch nach origin pushen. Rückgabe: Branch-Name."""
    repo = _require_repo(settings, project_id)
    if history_paused(settings, project_id):
        raise GitError("Der aktuelle Projektstand ist nicht vollständig im Verlauf. Push ist pausiert; bitte zuerst den Versionsspeicher freigeben.")
    url = remote_url(settings, project_id)
    if url is None:
        raise GitError("Es ist noch kein Remote konfiguriert — zuerst Remote setzen.")
    validate_remote_url(url, settings.git_allowed_hosts)
    branch = _current_branch(repo)
    with _askpass(token) as env:
        result = _git(repo, "-c", "http.followRedirects=false", "push", "origin", f"HEAD:{branch}", timeout=120, env=env)
    if result.returncode != 0:
        raise GitError(_remote_error("push", result.stderr.decode("utf-8", "replace")))
    return branch


@locked_project
def pull(settings: Settings, project_id: int, token: str | None) -> str:
    """Fast-forward pull von origin. Rückgabe: neuer HEAD (short)."""
    repo = _require_repo(settings, project_id)
    url = remote_url(settings, project_id)
    if url is None:
        raise GitError("Es ist noch kein Remote konfiguriert — zuerst Remote setzen.")
    validate_remote_url(url, settings.git_allowed_hosts)
    branch = _current_branch(repo)
    # Erst in einer Arbeitskopie laden: ein zu großes Remote darf den bisherigen
    # Verlauf weder ersetzen noch dauerhaft über das Budget anwachsen lassen.
    with tempfile.TemporaryDirectory(prefix=".pull-", dir=settings.git_root) as directory:
        staged = Path(directory) / "repo"
        shutil.copytree(repo, staged, symlinks=True)
        with _askpass(token) as env:
            result = _git(staged, "-c", "http.followRedirects=false", "pull", "--ff-only", "origin", branch, timeout=120, env=env)
        if result.returncode != 0:
            raise GitError(_remote_error("pull", result.stderr.decode("utf-8", "replace")))
        _check_remote_tree(staged)
        size = sum(p.stat().st_size for p in (staged / ".git").rglob("*") if p.is_file())
        if size > settings.history_max_bytes:
            raise GitError("Der Git-Verlauf des Remotes überschreitet das Speicherlimit. Bitte ein kleineres Repository verwenden.")
        previous = Path(directory) / "previous"
        repo.rename(previous)
        try:
            staged.rename(repo)
        except Exception:
            previous.rename(repo)
            raise
    return _out(_checked(repo, "rev-parse", "--short", "HEAD")).strip()


def head_short(settings: Settings, project_id: int) -> str | None:
    repo = repo_dir(settings, project_id)
    if not (repo / ".git").exists():
        return None
    result = _git(repo, "rev-parse", "--short", "HEAD")
    return _out(result).strip() if result.returncode == 0 else None


@locked_project
def reset_head(settings: Settings, project_id: int, ref: str) -> None:
    """ Arbeitsbaum hart auf einen Commit zurücksetzen (z. B. Quota-Rollback nach Pull)."""
    repo = _require_repo(settings, project_id)
    _checked(repo, "reset", "--hard", _check_commit(ref))
