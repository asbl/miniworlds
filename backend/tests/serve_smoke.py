"""Isolierte Instanz für browser-workflow.cjs, ohne Zugriff auf Nutzerdaten."""
import sys
import tempfile
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.main import create_app


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="miniworlds-browser-") as temporary:
        root = Path(temporary)
        settings = Settings(secret_key="browser-smoke-only", database_url=f"sqlite:///{root}/app.db",
                            media_root=str(root / "media"), git_root=str(root / "git"),
                            admin_email="admin@example.test", admin_password="local-test-password")
        application = create_app(settings, enable_yearly_task=False)
        uvicorn.run(application, host="127.0.0.1", port=8896, log_level="warning")
