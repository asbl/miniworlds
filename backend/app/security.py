from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from cryptography.fernet import Fernet

_ph = PasswordHasher()

# Alphabet ohne verwechselbare Zeichen (0/O, 1/I/L)
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, pw_hash: str) -> bool:
    try:
        return _ph.verify(pw_hash, password)
    except Exception:
        return False


def gen_code(length: int = 10) -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


def normalize_code(code: str) -> str:
    return code.strip().upper()


def hash_code(code: str) -> str:
    return hashlib.sha256(normalize_code(code).encode()).hexdigest()


def _fernet(secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_code(code: str, secret: str) -> str:
    return _fernet(secret).encrypt(code.encode()).decode()


def decrypt_code(enc: str, secret: str) -> str:
    return _fernet(secret).decrypt(enc.encode()).decode()


def encrypt_secret(value: str, secret: str) -> str:
    """z. B. git-Remote-Tokens — at rest verschlüsselt, nie an Clients zurückgegeben."""
    return _fernet(secret).encrypt(value.encode()).decode()


def decrypt_secret(enc: str, secret: str) -> str:
    return _fernet(secret).decrypt(enc.encode()).decode()


def encryption_key_check(secret: str) -> str:
    return hmac.new(secret.encode(), b"miniworlds-encryption-key-v1", hashlib.sha256).hexdigest()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(secret: str, session_token: str) -> str:
    return hmac.new(secret.encode(), (session_token + ":csrf").encode(), hashlib.sha256).hexdigest()


def make_student_token(secret: str, project_id: int, code_hash: str, hours: int) -> str:
    payload = {"pid": project_id, "ch": code_hash[:16], "exp": int(time.time()) + hours * 3600}
    b = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), b.encode(), hashlib.sha256).hexdigest()
    return f"{b}.{sig}"


def verify_student_token(secret: str, token: str) -> dict | None:
    try:
        b, sig = token.split(".")
        expected = hmac.new(secret.encode(), b.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if int(payload["exp"]) < time.time():
            return None
        return payload
    except Exception:
        return None


class RateLimiter:
    """Einfacher In-Memory-Limiter (ausreichend für einen einzelnen Prozess)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        with self._lock:
            dq = self._hits[key]
            while dq and now - dq[0] > window_seconds:
                dq.popleft()
            if len(dq) >= limit:
                return False
            dq.append(now)
            return True

    def limited(self, key: str, limit: int, window_seconds: int) -> bool:
        """Prüfen ohne erfolgreiche Anmeldungen als Fehlversuch zu zählen."""
        now = time.time()
        with self._lock:
            dq = self._hits.get(key)
            if not dq:
                return False
            while dq and now - dq[0] > window_seconds:
                dq.popleft()
            return len(dq) >= limit


rate_limiter = RateLimiter()
