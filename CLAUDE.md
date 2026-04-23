# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repository (`croogmandoo/BudgetApp`) has **no source code yet**. Product direction is captured in `SPEC.md`; implementation has not started.

When the first real code lands, replace this section with:
- Build / lint / test / run commands (including how to run a single test).
- High-level architecture that spans multiple files.
- Project-specific conventions that are not obvious from reading the code.

## Where to Look First

Read **`SPEC.md`** before suggesting anything. It captures locked-in product decisions with **[OPEN]** markers where decisions are still needed and **[SEC]** tags on security-sensitive items. The short version:

- **Scope:** self-hostable household finance + home-management app with four pillars — transaction tracking, envelope budgeting + bills, home projects, maintenance reminders.
- **Users:** multi-user household, household-wide data visibility, roles `admin` / `member` / `viewer`.
- **Stack:** Django 5 + Django REST Framework + SvelteKit + Postgres 16, delivered as a Docker Compose stack. Celery (or django-q2) + Redis for background jobs.
- **API:** first-class — REST + OpenAPI schema, per-user personal access tokens with scopes, outbound HMAC-signed webhooks. The SPA and external integrators share one API surface.
- **Security is a pillar.** Argon2id passwords, mandatory TOTP from day one, envelope encryption (master key in env wraps per-row / per-file DEKs), attachments encrypted at rest, CSRF + strict CSP, append-only audit log, `budgetapp backup` / `budgetapp restore` commands.
- **Import (v1):** file-based — CSV / OFX / QFX with declarative per-bank profiles for Amex Canada, CIBC, TD, RBC, Scotiabank. CAD primary, USD transactions round-trip via stored fx rate. Aggregator (Plaid or Flinks) deferred to M5.
- **Non-goals v1:** investment performance / tax lots, bill pay, receipt OCR, native mobile apps, Kubernetes deployment.

## License Posture

**Proprietary / all rights reserved.** No OSS license has been committed. Do not add a `LICENSE` file or `SPDX` headers without the owner's say-so — the project is not being released publicly yet. `SPEC.md` §8 documents the decision and lists the options to consider at first public release.

## Branch Convention

Feature work goes on `claude/<short-description>-<slug>` branches (see the branch instructions Claude Code sessions receive). `main` does not yet exist on the remote; the first merge target will be created when v1 implementation starts.

## Bootstrapping Guidance

If asked to scaffold the initial project:
- Work from `SPEC.md` — do not re-litigate decisions already locked in there.
- Mirror the stack exactly (Django 5, DRF, SvelteKit, Postgres 16, Docker Compose).
- First commits should set up: Django project skeleton, Postgres service in `docker-compose.yml`, SvelteKit app under `frontend/`, a basic CI that runs `pytest` + `ruff` + `svelte-check`.
- Add the lockfiles (`poetry.lock` / `uv.lock`, `pnpm-lock.yaml`) on the commit that introduces dependencies.
- Once the toolchain exists, replace the "Repository Status" section above with real commands and an architecture overview.
