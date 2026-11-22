"""Begrenzte Request-Bodies vor Parsern und Schreibsperren einlesen."""
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

from .services import MAX_MEDIA_FILE_BYTES


async def buffer_request(request, settings):
    path = request.url.path
    limit = settings.max_request_bytes if path == "/api/play/save" else 1024 * 1024
    if path == "/api/play/media":
        limit = MAX_MEDIA_FILE_BYTES + 128 * 1024
    try:
        length = int(request.headers.get("content-length", "0"))
        if length < 0:
            raise ValueError
    except ValueError:
        return JSONResponse({"detail": "Ungültige Inhaltslänge."}, status_code=400)
    if length > limit:
        return JSONResponse({"detail": "Anfrage ist zu groß."}, status_code=413)
    chunks, size = [], 0
    try:
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit:
                return JSONResponse({"detail": "Anfrage ist zu groß."}, status_code=413)
            chunks.append(chunk)
    except ClientDisconnect:
        return JSONResponse({"detail": "Übertragung wurde abgebrochen."}, status_code=400)
    # BaseHTTPMiddleware verwendet den Cache beim Weiterreichen an den Parser.
    request._body = b"".join(chunks)
    return None
