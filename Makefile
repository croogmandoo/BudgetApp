# BudgetApp — operator shortcuts around the Docker Compose stack.
#
# Run `make help` (or just `make`) to list the available targets.
# Pass arguments to `backend-manage` via ARGS, e.g.:
#   make backend-manage ARGS="createsuperuser"

.PHONY: help up down logs ps backend-shell backend-manage frontend-shell \
        migrate makemigrations test-backend test-frontend lint

# Default target: print usage so a bare `make` is never destructive.
help:
	@echo "BudgetApp — common targets:"
	@echo ""
	@echo "  make up                        Build images and start the stack in the background"
	@echo "  make down                      Stop and remove containers (keeps named volumes)"
	@echo "  make logs                      Tail logs for every service"
	@echo "  make ps                        Show container status"
	@echo ""
	@echo "  make backend-shell             Open a bash shell inside the app container"
	@echo "  make backend-manage ARGS=...   Run a Django management command (e.g. ARGS=\"createsuperuser\")"
	@echo "  make frontend-shell            Open an sh shell inside the frontend container"
	@echo ""
	@echo "  make migrate                   Apply Django migrations"
	@echo "  make makemigrations            Generate new Django migrations"
	@echo ""
	@echo "  make test-backend              Run backend pytest suite"
	@echo "  make test-frontend             Run frontend test suite (pnpm)"
	@echo "  make lint                      Run ruff + eslint across backend and frontend"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

backend-shell:
	docker compose exec app bash

backend-manage:
	docker compose exec app python manage.py $(ARGS)

frontend-shell:
	docker compose exec frontend sh

migrate:
	docker compose exec app python manage.py migrate

makemigrations:
	docker compose exec app python manage.py makemigrations

test-backend:
	docker compose exec app pytest

test-frontend:
	docker compose exec frontend pnpm test

lint:
	docker compose exec app ruff check .
	docker compose exec frontend pnpm lint
