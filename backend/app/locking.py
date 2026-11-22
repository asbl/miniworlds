"""Gemeinsame Schreibsperre für konsistente Sicherungen von DB und Dateien."""
import asyncio
import fcntl
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path


def _open_lock(settings):
    root = Path(settings.git_root)
    root.mkdir(parents=True, exist_ok=True)
    return (root / ".storage.lock").open("a")


@contextmanager
def storage_lock(settings, *, exclusive=False):
    with _open_lock(settings) as lock:
        fcntl.flock(lock, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield


@asynccontextmanager
async def async_write_lock(settings, *, exclusive=False):
    with _open_lock(settings) as lock:
        while True:
            try:
                fcntl.flock(lock, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                await asyncio.sleep(0.05)
        yield


@asynccontextmanager
async def project_write_lock(settings, project_id):
    # Gilt für die ganze Anfrage, einschließlich DB-Commit und anschließendem
    # Git-Commit. Ein eigener Lock vermeidet Rekursion mit gitstore-Locks.
    root = Path(settings.git_root)
    with (root / f".request-project-{project_id}.lock").open("a") as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                await asyncio.sleep(0.025)
        yield
