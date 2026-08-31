# OpenExec API.
#
# Build context is the REPO ROOT, not backend/ -- app/ imports `openexec`, so
# the engine has to be in the image alongside the service:
#
#   docker build -f backend/Dockerfile -t openexec-api .
#
# settings.json is excluded by .dockerignore and must be mounted at run time
# (see docker-compose.yml). Nothing here bakes credentials.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, from the requirements files alone, so editing source does
# not invalidate the (slow) install layer. requirements.txt at the root is what
# setup.py turns into install_requires; backend/requirements.txt is runtime-only
# -- pytest and moto live in requirements-dev.txt and stay out of this image.
COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r requirements.txt -r backend/requirements.txt

# Now the source. README.md is here because setup.py reads it for long_description.
COPY setup.py README.md ./
COPY openexec/ ./openexec/
COPY backend/ ./backend/

# --no-deps: everything install_requires names was installed above, and re-resolving
# would let a transitive bump slip in behind the cached layer.
RUN pip install -e . --no-deps

# app.main:app resolves `app` (from /app/backend) and `openexec` (from /app).
# backend/pytest.ini's `pythonpath = . ..` does the same thing for tests only.
ENV PYTHONPATH=/app/backend:/app
WORKDIR /app/backend

# Non-root. Done after the editable install so egg-info is already written.
RUN useradd --create-home --uid 10001 openexec && chown -R openexec:openexec /app
USER openexec

EXPOSE 8000

# No curl in python:slim, and adding it just for this is not worth the layer.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

# --workers 1 is REQUIRED, not a tuning choice. The live-SSE fan-out
# (app/services/event_bus.py) keeps subscribers in a module-level dict, and
# app/services/orchestration.py holds the run lock, the cancellation registry,
# and the captured event loop in process globals. With a second worker, a
# client can connect to a process that is not running the deliberation and see
# an empty live tail while the run proceeds invisibly elsewhere. Scaling out
# means moving that fan-out to a shared broker first.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
