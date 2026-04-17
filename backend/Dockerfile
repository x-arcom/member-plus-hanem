# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

# Build deps for psycopg2 + cryptography — kept off the final image
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src ./src

# Runtime user
RUN useradd --uid 10001 --create-home --no-log-init app \
 && chown -R app:app /app
USER app

EXPOSE 8000

# Healthcheck — hits the /health endpoint (not available until config is valid,
# so a config failure will surface as an unhealthy container).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "main:app", \
     "--app-dir", "src/app-entrypoint", \
     "--host", "0.0.0.0", "--port", "8000"]
