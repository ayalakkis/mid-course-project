# Task Tracker backend (FastAPI) - runtime image for the course's final-project checkpoint.
# Only the backend is containerized: the frontend is a static file with no build step
# (see README "Open the frontend"), so it is not part of this image.

FROM python:3.11-slim

# Don't cache .pyc files in an immutable image; flush stdout/stderr immediately so
# `docker logs` shows output as it happens instead of buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only copy what the running app needs. Tests, docs, scripts, and any local .env
# are deliberately excluded (see .dockerignore) - the image should not carry a
# secrets file or dev/test tooling into a runtime container.
COPY app/ ./app/

# Run as a non-root user rather than the container default root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8000

# No curl/wget in the slim image, so check with the stdlib instead of shelling out.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
