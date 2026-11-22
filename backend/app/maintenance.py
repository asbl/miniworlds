"""Periodische Wartung außerhalb der HTTP-Verarbeitung."""
import fcntl
from pathlib import Path

from .retention import maybe_retention
from .locking import storage_lock
from .yearly import maybe_yearly_reset


def run_maintenance(session_factory, settings):
    # Prozessübergreifend: mehrere Uvicorn-Worker dürfen nicht parallel löschen.
    lock_path = Path(settings.git_root) / ".maintenance.lock"
    with storage_lock(settings, exclusive=True), lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        with session_factory() as db:
            maybe_yearly_reset(db)
            maybe_retention(db, settings)
