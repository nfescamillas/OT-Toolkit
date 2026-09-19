# syntax=docker/dockerfile:1

FROM node:24-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/vite.config.js ./vite.config.js
COPY frontend/web ./web
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OT_TOOLKIT_DATABASE_URL=sqlite+pysqlite:////data/ot_toolkit.db \
    OT_TOOLKIT_STATIC_DIR=/app/static

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY frontend/src ./frontend/src
RUN python -m pip install --no-cache-dir . \
    && addgroup --system ottoolkit \
    && adduser --system --ingroup ottoolkit --home /app ottoolkit \
    && mkdir -p /data \
    && chown ottoolkit:ottoolkit /data

COPY --from=frontend-builder /build/frontend/dist-web ./static

USER ottoolkit
EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/technologies', timeout=3)"

CMD ["uvicorn", "ot_toolkit_backend.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
