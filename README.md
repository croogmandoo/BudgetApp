# BudgetApp

Self-hostable household finance and home-management app: transaction tracking, envelope budgeting, home projects, and maintenance reminders — for one household, on your own hardware.

**Proprietary — all rights reserved.** No open-source license has been granted. See `SPEC.md` §8 for the licensing posture.

The product specification — locked-in decisions, scope, data model, security model — lives in [`SPEC.md`](./SPEC.md). It is the source of truth; if this README and the spec disagree, the spec wins.

## Stack

Django 5 + Django REST Framework, SvelteKit, Postgres 16, Redis + Celery, delivered as a Docker Compose stack.

## Quickstart

Requires Docker Engine with the Compose v2 plugin, and `make`.

```sh
git clone <this-repo> BudgetApp
cd BudgetApp
cp .env.example .env
# Edit .env and replace every REPLACE_ME value. See the comments in .env.example
# for how to generate APP_MASTER_KEY and DJANGO_SECRET_KEY.
make up
```

Once the stack is healthy, open [http://localhost:3000](http://localhost:3000) for the SPA. The REST API is at [http://localhost:8000/api/v1](http://localhost:8000/api/v1) and OpenAPI docs at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

First-run setup (create the admin user, enrol TOTP) happens through the web UI.

## Directory map

| Path                  | Purpose                                                            |
| --------------------- | ------------------------------------------------------------------ |
| `backend/`            | Django 5 + DRF project. Contains `budgetapp.asgi` and Celery app.  |
| `frontend/`           | SvelteKit SPA.                                                     |
| `.github/`            | CI workflows (pytest, ruff, svelte-check).                         |
| `docker-compose.yml`  | Four-service stack: `db`, `redis`, `app`, `worker`, `frontend`.    |
| `.env.example`        | Template for required environment variables.                       |
| `Makefile`            | Operator shortcuts around `docker compose`.                        |
| `SPEC.md`             | Product specification — the source of truth.                       |
| `CLAUDE.md`           | Guidance for Claude Code sessions working in this repo.            |

## Common commands

All day-to-day operations are wrapped by the `Makefile`. Run `make help` for the full list. Highlights:

- `make up` / `make down` — start / stop the stack.
- `make logs` — tail logs across every service.
- `make migrate` — apply Django migrations.
- `make backend-manage ARGS="createsuperuser"` — run an arbitrary Django management command.
- `make test-backend` / `make test-frontend` — run the test suites inside their containers.
- `make lint` — ruff + eslint across the repo.
