# BudgetApp — Specification (Draft)

> **Status:** Early draft. Sections marked **[OPEN]** need product decisions before implementation can start. Security-sensitive items are tagged **[SEC]**.

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
- Transaction model: date, amount, payee, memo, account, category, tags, split children, attached receipt.
- **Import** — **[OPEN]** Pick one or more:
  - (a) File import only: CSV / OFX / QFX / QIF (simplest, no third-party dep).
  - (b) Direct aggregator: SimpleFIN (self-host-friendly, paid), GoCardless/Nordigen (EU), Plaid (US, heavyweight), TrueLayer.
  - (c) Both — manual file import + optional aggregator.
- Manual entry + edit always available.
- **Categorization:**
  - Hierarchical categories (e.g. `Auto > Fuel`).
  - Rule engine: match on payee/memo/amount/account → assign category + tags. Rules are re-runnable.
  - **[OPEN]** Do we want YNAB-style envelope budgeting, or just category reporting?
  - **[OPEN]** Splits (one transaction → multiple categories)?
- Multi-currency — **[OPEN]** needed, or single-currency per instance?

### 3.2 Recurring Obligations ("Bills")
- Bill = name, payee, amount (fixed or variable), cadence (monthly/quarterly/annual/custom), due day, account it pays from, optional auto-pay flag.
- Monthly view: expected vs. paid, overdue highlights.
- **Matching:** when a transaction comes in that matches a bill (payee + amount range + date window), mark the bill paid and link the transaction. Manual override always available.
- Projection: upcoming 30/60/90-day cash-flow forecast from recurring bills + scheduled income.

### 3.3 Home Projects
- Project = name, status (planned/active/done/abandoned), budget, start/end dates, notes.
- Sub-tasks with status, estimated cost, actual cost, assignee (if multi-user), due date.
- **Cost rollup:** sum of sub-task actuals + directly-linked transactions.
- Attachments: receipts, quotes, photos, PDFs. **[SEC]** Stored locally by default; see §7 on encryption.
- Vendor/contractor contacts attachable to project or sub-task.

### 3.4 Maintenance Reminders
- Recurring task: title, cadence (time-based: every N months; OR usage-based **[OPEN]** e.g. odometer), last-done date, next-due date, notes/checklist.
- Completing a task logs the completion (with optional cost → creates/links a transaction) and schedules the next occurrence.
- **Notification channels** — **[OPEN]** In-app only? Email? Push via ntfy/Gotify? Matrix? Which is acceptable for a self-host audience?

### 3.5 Reporting
- Monthly spend by category, trend lines, year-over-year.
- Net worth over time (accounts' running balances).
- Project totals (actual vs. budget).
- CSV export of any filtered transaction list.

## 4. Non-Goals (initially)

- Investment performance tracking, tax-lot accounting.
- Bill pay / moving money (read-only + record-keeping only).
- Receipt OCR (nice-to-have, later).
- Mobile native apps (PWA is the mobile story unless stated otherwise).

## 5. Architecture (proposed, pending stack decision)

- **Deployment target:** single `docker compose up` on a home server (Linux x86_64 + arm64). **[OPEN]** Confirm.
- **Data store:** **[OPEN]** SQLite (simplest self-host, great for single-household) vs. Postgres (multi-user scale, more ops burden). Recommendation: SQLite with WAL; revisit if we ever need >1 node.
- **Backend language/framework:** **[OPEN]** — see §9.
- **Frontend:** **[OPEN]** SPA (React/Svelte) vs. server-rendered + HTMX. HTMX leans simpler for self-host; SPA better for PWA/offline.
- **Background jobs:** recurring bill materialization, reminder scheduling, aggregator sync. In-process scheduler is fine for single-instance deploys.
- **File storage:** local filesystem volume for attachments (S3 optional later).
- **Config:** environment variables + a single config file; secrets via env or Docker secrets.

## 6. Data Model Sketch (informational)

- `user` — id, email, password_hash, totp_secret_enc, roles.
- `account` — id, name, type, institution, currency, starting_balance, closed_at.
- `transaction` — id, account_id, date, amount, payee, memo, category_id, status, import_hash, receipt_id.
- `transaction_split` — parent_transaction_id, category_id, amount, memo.
- `category` — id, parent_id, name, kind (income/expense/transfer).
- `rule` — id, priority, match_json, action_json, enabled.
- `bill` — id, name, payee, amount, cadence, next_due, account_id, autopay.
- `bill_instance` — id, bill_id, due_date, amount_expected, paid_transaction_id, status.
- `project` — id, name, status, budget, notes.
- `project_task` — id, project_id, title, status, est_cost, actual_cost, due_date.
- `project_transaction_link` — project_id/task_id ↔ transaction_id.
- `attachment` — id, owner_type, owner_id, filename, mime, size, sha256, path_or_blob, encrypted.
- `maintenance_task` — id, title, cadence, last_done, next_due, checklist_json.
- `audit_log` — id, user_id, at, action, entity, before_hash, after_hash, ip.

## 7. Security [SEC]

Treated as a pillar. Baseline requirements:

### 7.1 AuthN / AuthZ
- Password auth with Argon2id hashing.
- **[OPEN]** Multi-user (household members with per-user roles) or single-user v1? This gates the whole auth model.
- **Mandatory** TOTP (RFC 6238) for all users; optional WebAuthn/passkeys as a follow-up. **[OPEN]** Confirm TOTP-mandatory from day one.
- Session tokens: HTTP-only, Secure, SameSite=Lax cookies; rotation on privilege change; idle + absolute timeouts.
- Rate limiting + account lockout on login.

### 7.2 Data at Rest
- DB file permissions 0600; container runs non-root.
- **Field-level encryption** for sensitive columns: account numbers, aggregator access tokens, TOTP secrets, attachments containing PII. Key from env/KMS, not DB.
- Attachments: **[OPEN]** encrypt at rest by default? (Leaning yes — these are receipts with account numbers and addresses.)
- Backups: documented `sqlite3 .backup` / `pg_dump` workflow; encrypted before leaving the host. **[OPEN]** Bundled backup job, or leave to the operator?

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
- **In scope:** casual attacker on LAN, stolen laptop/backup, compromised dependency, XSS/CSRF/SQLi, malicious file upload.
- **Out of scope v1:** nation-state, host-level compromise of the server itself (if root is owned, the DB key in env is owned too — documented limitation).
- **[OPEN]** Should the master encryption key be held by the user (prompted at startup, never stored), accepting the UX cost of re-entry after reboot?

## 8. Operational Concerns

- First-run setup wizard: create admin user, enroll TOTP, set encryption key, choose import method.
- Upgrade path: versioned migrations, pre-migration backup.
- Observability: structured logs, health endpoint, optional Prometheus metrics.
- License: **[OPEN]** (AGPL-3.0 is typical for self-host-first projects; MIT if you want max adoption.)

## 9. Open Stack Decisions

| Area | Options | Notes |
|---|---|---|
| Backend | Go, Rust (Axum), Python (FastAPI/Django), TS (Node/Bun), Kotlin (Ktor) | Go & Rust give single-binary deploys; Django brings admin+auth batteries. |
| Frontend | React, Svelte/SvelteKit, HTMX + server templates, Vue | HTMX easiest for self-host simplicity. |
| DB | SQLite, Postgres | SQLite recommended for v1. |
| Container runtime | Docker Compose, Podman | Compose primary; Podman-compatible. |

## 10. Milestones (tentative)

1. **M0 – Foundations.** Auth (password + TOTP), user/account/category/transaction CRUD, CSV import, categorization rules.
2. **M1 – Bills & forecast.** Recurring bills, matching, 30-day forecast.
3. **M2 – Home projects.** Projects, tasks, attachments, transaction linking.
4. **M3 – Maintenance.** Recurring tasks, notifications.
5. **M4 – Reports & polish.** Trends, exports, PWA.
6. **M5 – Optional aggregator.** Pick one of SimpleFIN/GoCardless/Plaid behind a feature flag.

---

## Questions I Need Answered Before Going Deeper

Please answer (or say "defer") for each:

1. **Users:** Single user, or multiple household members with separate logins? If multiple, does everyone see everything, or per-account permissions?
2. **Transaction import:** File-only (CSV/OFX) for v1, or is an aggregator (SimpleFIN / GoCardless / Plaid) in scope? If aggregator, which region(s) do you bank in?
3. **Budgeting style:** Plain category reporting, or envelope/zero-based budgeting (YNAB-style)?
4. **Stack preference:** Any language/framework you already know and want to self-host, or should I recommend? Hard preferences on SQLite vs. Postgres, SPA vs. server-rendered?
5. **Notifications:** In-app only OK for v1, or do you want email / push (ntfy, Gotify, etc.) from the start?
6. **Encryption key custody:** Convenient (key in env, survives reboots) or paranoid (key entered at startup, app locked until you unlock it)?
7. **Attachments:** Encrypt at rest by default — confirm yes?
8. **Multi-currency:** Single currency per instance OK, or must support multiple?
9. **License:** AGPL-3.0, MIT, something else, or defer?
10. **Deployment:** Docker Compose on a home Linux box is the target — any other environment (Unraid, TrueNAS app, Kubernetes, bare metal) that must work on day one?
