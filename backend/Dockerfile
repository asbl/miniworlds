# Build-Kontext ist das Repository; das Player-Wheel wird immer mitgebaut.
FROM python:3.12-slim AS wheel
WORKDIR /build
COPY source ./source
RUN pip wheel --no-deps ./source --wheel-dir /wheels

FROM python:3.12-slim

# git wird für den serverseitigen Versionsverlauf (Versionsverlauf im Player) benötigt
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=wheel /wheels /tmp/wheels
RUN mkdir -p app/static/wheel && cp /tmp/wheels/miniworlds-*.whl app/static/wheel/miniworlds.whl && rm -rf /tmp/wheels \
    && chmod -R a+rX /app \
    && groupadd --gid 10001 miniworlds && useradd --uid 10001 --gid miniworlds --no-create-home miniworlds \
    && mkdir -p /data /backups && chown miniworlds:miniworlds /data /backups

ENV DATABASE_URL=sqlite:////data/app.db \
    MEDIA_ROOT=/data/media \
    MINIWORLDS_GIT_ROOT=/data/git \
    BASE_URL=http://localhost:8000 \
    COOKIE_SECURE=1 \
    PYTHONDONTWRITEBYTECODE=1

VOLUME ["/data"]
EXPOSE 8000
USER 10001:10001
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"

# Secret + Admin-Seed kommen aus der Umgebung (siehe README)
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
