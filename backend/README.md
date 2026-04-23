# BudgetApp Backend

Django 5 + Django REST Framework backend for the BudgetApp household finance
app. See [`../SPEC.md`](../SPEC.md) for the product specification, locked-in
decisions, and security requirements.

This directory is the API/service tier. The SvelteKit SPA under `../frontend/`
consumes the same REST API that external integrators use.

## Quickstart (local development)

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/), Postgres 16, and
Redis running locally (or via the project-root `docker-compose.yml`).

```bash
uv sync
cp .env.example .env   # if present; otherwise export the vars listed below
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

Required environment variables (see `budgetapp/settings.py` for the full list):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`0` or `1`)
- `DATABASE_URL` (e.g. `postgres://user:pass@localhost:5432/budgetapp`)
- `REDIS_URL` (e.g. `redis://localhost:6379/0`)
- `APP_MASTER_KEY` (used for envelope encryption of sensitive columns and
  attachments; see SPEC §7.2)
- `ALLOWED_HOSTS` (comma-separated)
- `CSRF_TRUSTED_ORIGINS` (comma-separated)
- `FRONTEND_URL`

## Layout

- `budgetapp/` — Django project (settings, URLs, ASGI/WSGI, Celery wiring).
- `apps/` — Django apps grouped by domain (accounts, finances, budgets,
  bills, projects, maintenance, notifications, core).

## API

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`
- Versioned endpoints: `/api/v1/...`

## Background jobs

Celery worker:

```bash
uv run celery -A budgetapp worker --loglevel=info
```

Celery beat (for scheduled reminders / recurring bill materialization):

```bash
uv run celery -A budgetapp beat --loglevel=info
```

## Tests / lint / type-check

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

## License

Proprietary — all rights reserved. See SPEC §8.
