# BudgetApp — Specification (Draft)

> **Status:** Draft, revision 3. Sections marked **[OPEN]** need product decisions before implementation can start. Security-sensitive items are tagged **[SEC]**.

## 0. Decisions Locked In (rev 3)

- **Multi-user** household; **household-wide data visibility** — every member sees every shared account/debt/project (this instance exists for shared finances).
- **Import:** file-based primary (CSV/OFX/QFX); aggregator (Plaid or Flinks for Canadian coverage) is M5.
- **Banks targeted at launch:** Amex Canada, CIBC, TD, RBC, Scotiabank. Primary currency **CAD**; USD transactions must round-trip cleanly.
- **Stack:** **Django 5 + Django REST Framework + SvelteKit + Postgres 16**, delivered as a Docker Compose stack (app + db + redis/worker containers).
- **TOTP mandatory** for all users from day one.
- **Budgeting model:** category reporting **plus** envelope/YNAB-style allocations layered on top (categories act as envelopes when a budget is set for a period; reports work either way).
- **Encryption-key custody:** convenient — master key lives in env/secret, app starts unattended after reboot.

## 1. Vision

A self-hostable personal finance + home-management app for a household. Four pillars:

1. **Spending** — import transactions from accounts, categorize them (manually + via rules), and review.
2. **Recurring obligations** — track monthly/annual bills (mortgage, utilities, subscriptions) with due dates and payment status.
3. **Home projects** — project boards with sub-tasks, costs, receipts, and linked transactions.
4. **Maintenance reminders** — recurring upkeep tasks (HVAC filter, gutters, smoke-alarm batteries, vehicle service).

Security is a first-class pillar, not an afterthought (see §7).

## 2. Primary User Stories

- As the owner, I import my month's transactions from my bank, see uncategorized ones flagged, and apply or create rules to auto-categorize them.
- I see a dashboard of this month's fixed obligations, which are paid, which are due, and the projected end-of-month cash position.
- I create a "Finish basement" project, add sub-tasks (demo, framing, electrical), attach quotes/receipts, and the project shows total spend pulled from linked transactions.
- I get a reminder that the HVAC filter is due and mark it done; the next occurrence schedules automatically.

## 3. Functional Scope

### 3.1 Accounts & Transactions
- Multiple accounts (checking, savings, credit card, cash, loan). **[OPEN]** Investment/brokerage accounts in scope?
- Transaction model: date, amount, payee, memo, account, category, tags, split children, attached receipt, original-currency + fx-rate fields.
- **Import (v1):** file-based.
  - Supported formats: **CSV** (per-bank profile), **OFX / QFX** where the bank offers it.
  - **Per-bank CSV profiles** shipped at launch (schemas differ across Canadian banks):
    - **Amex Canada** — CSV from the web portal.
    - **CIBC** — CSV export (credit card + chequing have different layouts).
    - **TD** — CSV (EasyWeb export).
    - **RBC** — CSV (Online Banking export).
    - **Scotiabank** — CSV.
  - Each profile is a declarative mapping (columns → transaction fields, sign convention, date format, encoding) so new banks can be added without code changes.
  - **De-duplication** on import: stable hash of (account, date, amount, normalized payee) + explicit "already imported" detection on re-upload.
  - Manual entry + edit always available.
- **Import (later milestone):** aggregator integration. Canadian coverage options: **Plaid** (has CA support for major banks), **Flinks** (Canadian-native), **MX**. SimpleFIN/GoCardless do not cover Canadian retail banks reliably. Decision deferred to M5.
- **Categorization:**
  - Hierarchical categories (e.g. `Auto > Fuel`).
  - Rule engine: match on payee/memo/amount/account → assign category + tags. Rules are re-runnable over historical transactions.
  - Splits supported — one transaction can be divided across multiple categories (needed for Costco-style mixed baskets).
- **Multi-currency:** primary currency **CAD**; transactions may carry a different `original_currency` + `fx_rate_at_time`. Reports default to CAD using stored rates; no live FX feed in v1.

### 3.2 Budgeting (Categories + Envelopes)
Two layers, both always available:

1. **Category reporting** (passive) — every transaction has a category; reports aggregate spend by category and period.
2. **Envelope budgeting** (active) — for each monthly period, an amount can be allocated to a category ("envelope"). That category then has a running balance = carry-in + allocations − spend.

Rules:
- Period = calendar month, household timezone.
- Categories have an `is_budgetable` flag. Non-budgetable categories (e.g. `Transfers`, `Reimbursements`) never draw from an envelope.
- **Rollover behaviour per category:** `carry_positive` (unspent rolls forward — default for sinking funds like `Auto > Maintenance`), `carry_negative` (overspend rolls forward as a debt against next month — default for typical spending), or `reset` (balance zeroes each month — default for allowances).
- **Moving money between envelopes** is a first-class action with its own audit record; doesn't create a fake transaction.
- **Income flow:** income transactions add to a pool ("to-be-budgeted") until the user allocates them. The top bar always shows to-be-budgeted so it can't be silently overspent.
- Splits respect envelopes: each split draws from its own category's envelope.
- Reports: both "spend by category" (reporting mode) and "envelope status this month" (budgeting mode) views.

Opt-out: a household can ignore allocations entirely and still use categories for reporting — envelopes only activate when an allocation is set.

### 3.3 Recurring Obligations ("Bills")
- Bill = name, payee, amount (fixed or variable), cadence (monthly/quarterly/annual/custom), due day, account it pays from, optional auto-pay flag.
- Monthly view: expected vs. paid, overdue highlights.
- **Matching:** when a transaction comes in that matches a bill (payee + amount range + date window), mark the bill paid and link the transaction. Manual override always available.
- Projection: upcoming 30/60/90-day cash-flow forecast from recurring bills + scheduled income.

### 3.4 Home Projects
- Project = name, status (planned/active/done/abandoned), budget, start/end dates, notes.
- Sub-tasks with status, estimated cost, actual cost, assignee (if multi-user), due date.
- **Cost rollup:** sum of sub-task actuals + directly-linked transactions.
- Attachments: receipts, quotes, photos, PDFs. **[SEC]** Stored locally by default; see §7 on encryption.
- Vendor/contractor contacts attachable to project or sub-task.

### 3.5 Maintenance Reminders
- Recurring task: title, cadence (time-based: every N months; usage-based e.g. odometer km/miles is a stretch goal), last-done date, next-due date, notes/checklist.
- Completing a task logs the completion (with optional cost → creates/links a transaction) and schedules the next occurrence.
- **Notification channels** — **[OPEN]** In-app is guaranteed. Which additional channel(s) day one: email (SMTP), ntfy, Gotify, webhook? (Webhook falls out of the API pillar almost for free.)

### 3.6 Reporting
- Monthly spend by category, trend lines, year-over-year.
- Net worth over time (accounts' running balances).
- Project totals (actual vs. budget).
- CSV export of any filtered transaction list.

## 4. Non-Goals (initially)

- Investment performance tracking, tax-lot accounting.
- Bill pay / moving money (read-only + record-keeping only).
- Receipt OCR (nice-to-have, later).
- Mobile native apps (PWA is the mobile story unless stated otherwise).

## 5. Architecture (proposed)

- **Deployment target:** single `docker compose up` on a home server (Linux x86_64 + arm64). **[OPEN]** Any other targets that must work day one (Unraid app, TrueNAS SCALE, Kubernetes)?
- **Data store:** **Postgres 16.** Multi-user + concurrent writes + JSONB for rule payloads + strong transactional guarantees justify the ops cost over SQLite.
- **Backend:** see §9 for the proposed stack.
- **Frontend:** SPA that consumes the same public REST API that external tools will use (see §5.1). This keeps a single API surface rather than a "private web API + public integration API" split.
- **Background jobs:** recurring bill materialization, reminder dispatch, future aggregator sync, import processing. Single-process scheduler (e.g. Celery-beat, APScheduler, or framework-native) acceptable for household scale.
- **File storage:** local filesystem volume for attachments, encrypted at rest (see §7.2). S3-compatible backend optional later.
- **Config:** environment variables + optional file; secrets via env or Docker secrets.

### 5.1 API as a First-Class Surface
The user called out external integrations as a requirement, so the API is not an afterthought:
- **REST + OpenAPI 3.1** schema generated from source of truth; schema served at `/api/schema` and rendered via Swagger UI / Redoc at `/api/docs`.
- **Auth for API clients:** personal access tokens (PATs) scoped per-user, revocable, with optional scopes (`transactions:read`, `bills:write`, etc.). Session cookies used for the SPA; PATs for everything else.
- **Versioning:** URL-prefixed (`/api/v1/...`). Breaking changes require a new version.
- **Webhooks (outbound):** configurable HTTP callbacks on events (`transaction.imported`, `bill.overdue`, `maintenance.due`) with HMAC-signed payloads. Lets the app talk to Home Assistant, n8n, etc.
- **Rate limiting** per token.

## 6. Data Model Sketch (informational)

- `household` — id, name, base_currency (default `CAD`).
- `user` — id, household_id, email, password_hash, totp_secret_enc, role (`admin` / `member` / `viewer`), disabled_at.
- `api_token` — id, user_id, name, token_hash, scopes, last_used_at, revoked_at.
- `account` — id, household_id, name, type, institution, currency, starting_balance, closed_at.
- `import_profile` — id, institution, format (`csv` / `ofx`), mapping_json (columns → fields, date fmt, sign convention).
- `import_batch` — id, account_id, user_id, filename, sha256, row_count, created_at.
- `transaction` — id, account_id, date, amount, original_currency, fx_rate, payee, memo, category_id, status, import_batch_id, import_hash, receipt_attachment_id.
- `transaction_split` — parent_transaction_id, category_id, amount, memo.
- `category` — id, household_id, parent_id, name, kind (income / expense / transfer), is_budgetable, rollover_mode (`carry_positive` / `carry_negative` / `reset`).
- `budget_period` — id, household_id, month (date, first-of-month), locked_at.
- `budget_allocation` — id, period_id, category_id, amount. Uniqueness on (period_id, category_id).
- `budget_transfer` — id, period_id, from_category_id, to_category_id, amount, memo, user_id, at. (Audit-visible "move money between envelopes".)
- `rule` — id, household_id, priority, match_json, action_json, enabled.
- `bill` — id, household_id, name, payee, amount, cadence, next_due, account_id, autopay.
- `bill_instance` — id, bill_id, due_date, amount_expected, paid_transaction_id, status.
- `project` — id, household_id, name, status, budget, notes.
- `project_task` — id, project_id, title, status, est_cost, actual_cost, due_date, assignee_user_id.
- `project_transaction_link` — project_id / task_id ↔ transaction_id.
- `attachment` — id, owner_type, owner_id, filename, mime, size, sha256, encrypted_blob_ref, dek_enc (envelope-encryption wrap of data-encryption key).
- `maintenance_task` — id, household_id, title, cadence, last_done, next_due, checklist_json.
- `webhook` — id, household_id, url, secret_enc, event_mask, enabled.
- `audit_log` — id, household_id, user_id, at, action, entity, before_hash, after_hash, ip, user_agent.

## 7. Security [SEC]

Treated as a pillar. Baseline requirements:

### 7.1 AuthN / AuthZ
- **Model:** one `household` per instance; each user belongs to a household and has a role. **Data visibility is household-wide** — every member sees every shared account, bill, project, and envelope. No per-account hiding in v1.
  - `admin` — manages users, accounts, categories, import profiles, webhooks, encryption-key rotation.
  - `member` — full read/write on transactions, bills, projects, maintenance, budgets.
  - `viewer` — read-only.
- Password auth with Argon2id hashing.
- **TOTP (RFC 6238) is mandatory** for all users from first login. WebAuthn/passkey support follows later.
- API clients authenticate with personal access tokens (see §5.1), not password+TOTP.
- Session tokens: HTTP-only, Secure, SameSite=Lax cookies; rotation on privilege change; idle + absolute timeouts.
- Rate limiting + progressive backoff on login (no hard lockout — avoids trivial DoS of a household member).

### 7.2 Data at Rest
- Postgres runs in its own container; volume permissions locked to the DB user; app container non-root.
- **Envelope encryption** for sensitive columns and all attachments:
  - Master key (`APP_MASTER_KEY`) in env/Docker secret — "convenient" custody, as chosen.
  - Per-row or per-file data-encryption keys (DEKs) encrypted by the master key, stored alongside the ciphertext.
  - Sensitive columns: aggregator tokens (future), TOTP secrets, API-token hashes are already hashed, payees can be treated as PII in reports.
  - Attachments encrypted at rest **by default** (receipts carry names, addresses, partial PANs). **[OPEN]** Confirm.
- Key rotation: `APP_MASTER_KEY` rotatable via a maintenance command that re-wraps DEKs without touching ciphertext.
- Backups: documented `pg_dump` workflow; a bundled `budgetapp backup` command produces an encrypted, timestamped artifact the operator can ship to off-host storage. **[OPEN]** Confirm the bundled command is wanted (vs. pure docs).

### 7.3 Data in Transit
- HTTPS required. App refuses to start without TLS config OR an explicit `BEHIND_TLS_PROXY=1` flag (for Caddy/Traefik users). HSTS when terminating TLS itself.
- Aggregator calls over TLS with pinned CA set.

### 7.4 Application Hardening
- CSRF tokens on state-changing requests.
- Strict CSP, no inline scripts, `frame-ancestors 'none'`.
- All queries parameterized; ORM or query builder, never string concat.
- Input validation at the boundary; output encoding in templates.
- Attachment handling: MIME sniffing on upload, size caps, served from a no-exec path with `Content-Disposition: attachment` + random filenames.
- Dependency pinning + automated vulnerability scanning (e.g. Dependabot, `govulncheck`, `cargo audit`).
- SBOM generated on release.

### 7.5 Audit & Transparency
- Append-only audit log of auth events, rule changes, manual balance adjustments, and attachment uploads.
- Exportable activity log per user.

### 7.6 Threat Model (initial)
- **In scope:** casual attacker on LAN, stolen laptop/backup, compromised dependency, XSS/CSRF/SQLi, malicious file upload, stolen API token.
- **Out of scope v1:** nation-state, host-level compromise of the server itself. Because the master key lives in env (per the "convenient" choice), host-root = data compromise. This is an accepted, **documented** trade-off; paranoid mode (prompt-at-startup) can be added later behind a flag without breaking the data model.

## 8. Operational Concerns

- First-run setup wizard: create admin user, enroll TOTP, set encryption key, choose import method.
- Upgrade path: versioned migrations, pre-migration backup.
- Observability: structured logs, health endpoint, optional Prometheus metrics.
- License: **[OPEN]** (AGPL-3.0 is typical for self-host-first projects; MIT if you want max adoption.)

## 9. Proposed Stack (needs confirmation)

Optimising for "robust + nice UI + API-first" with multi-user auth:

| Area | Recommendation | Why |
|---|---|---|
| Backend | **Django 5 + Django REST Framework** | Mature, security-hardened defaults (CSRF, auth, password hashing, ORM). Multi-user, admin panel, migrations, permissions all built in. DRF produces clean REST APIs with auto OpenAPI. |
| 2FA / MFA | **django-otp** (TOTP) + **django-webauthn** later | Maintained, integrates cleanly with Django sessions. |
| Background jobs | **Celery + Redis** (or **django-q2** for simpler setup) | Reminder dispatch, webhook delivery, import parsing. |
| Frontend | **SvelteKit** SPA consuming DRF | Less boilerplate than React, great DX, PWA-friendly. Same API external tools use → no duplication. |
| DB | **Postgres 16** | Justified by multi-user + JSONB rule payloads. |
| Attachments | Local volume, encrypted at rest | S3-compatible backend optional later. |
| Container | **Docker Compose** (Podman-compatible) | Target for home servers. |

**Alternatives** if you'd prefer:
- **End-to-end TypeScript:** NestJS + Prisma + Postgres + SvelteKit. Slightly more "hand-built" on the security side (you wire auth/CSRF yourself rather than inheriting Django's defaults).
- **Single binary:** Go (chi + sqlc) + SvelteKit built-in embed. Fewer moving parts at runtime, more security wiring up-front.

**Confirmed** (rev 3): Django 5 + DRF + SvelteKit + Postgres 16, delivered as a Docker Compose stack (separate containers: `app`, `worker`, `postgres`, `redis`).

## 10. Milestones (tentative)

1. **M0 – Foundations.** Household + users + roles, password + mandatory TOTP, API tokens, account/category/transaction CRUD, CSV import with CIBC + TD + RBC + Scotia + Amex profiles, categorization rules, OpenAPI docs.
2. **M1 – Budgeting & bills.** Envelope allocations (category + rollover + transfers + to-be-budgeted), recurring bills, transaction-to-bill matching, 30/60/90-day cash-flow forecast.
3. **M2 – Home projects.** Projects, sub-tasks, encrypted attachments, transaction linking, cost rollup.
4. **M3 – Maintenance + notifications.** Recurring maintenance tasks, in-app notifications, at least one external channel (email or ntfy), outbound webhooks.
5. **M4 – Reports & polish.** Trends, net-worth over time, CSV exports, PWA.
6. **M5 – Aggregator (optional).** Evaluate Plaid vs. Flinks for Canadian bank coverage behind a feature flag.

---

## Remaining Open Questions

Resolved in rev 3: sharing model, stack, TOTP, budgeting style (in addition to rev 2's user model, import, banks, key custody, currency). What's still needed:

1. **Notifications** — besides in-app, which of {SMTP email, ntfy, Gotify, webhook} should ship in M3? (Webhook is nearly free given the API-first design.)
2. **Attachments at rest** — encrypted by default (recommended, since receipts are PII-heavy) — confirm yes?
3. **Bundled backup command** — include a `budgetapp backup` command that produces an encrypted dump, or leave backups entirely to the operator's `pg_dump`?
4. **License** — AGPL-3.0 (typical for self-host-first), MIT (maximum adoption), something else, or defer?
5. **Deployment targets besides Docker Compose** — anything else that must work on day one (Unraid, TrueNAS SCALE, Kubernetes, bare-metal systemd)?
6. **Investment/brokerage accounts** — in scope for balance tracking only (no performance), or fully out for v1?
