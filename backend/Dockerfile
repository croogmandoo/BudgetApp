# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Stage 1: build virtualenv with uv.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned via the official installer).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project metadata first for cache-friendly dependency install.
# README.md is referenced by pyproject.toml's [project].readme and hatchling
# validates its presence during build, even for editable installs.
COPY pyproject.toml README.md ./
# Lock file is optional on initial scaffold; copy when present.
COPY uv.loc[k] ./
# Empty package directories so `uv pip install -e .` resolves before we copy
# the real source in the runtime stage.
RUN mkdir -p budgetapp apps \
    && touch budgetapp/__init__.py apps/__init__.py

# Install into an explicit venv path without sourcing the bash-only
# activate script (RUN defaults to /bin/sh, which on Debian-slim is dash
# and chokes on the activate script's bash-specific syntax).
RUN uv venv /opt/venv \
    && if [ -f uv.lock ]; then \
         uv sync --no-dev --frozen; \
       else \
         uv pip install --python /opt/venv/bin/python -e .; \
       fi

# ---------------------------------------------------------------------------
# Stage 2: runtime image.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=budgetapp.settings

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "budgetapp.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
