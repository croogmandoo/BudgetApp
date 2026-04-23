# BudgetApp Frontend

SvelteKit SPA for BudgetApp — a self-hostable household finance + home-management app.
See the root [`SPEC.md`](../SPEC.md) for product scope and architecture (especially
sections 5 and 5.1 on the API-first design). The frontend consumes the same public
REST API that external integrators use.

Proprietary — all rights reserved. See `SPEC.md` section 8.

## Stack

- SvelteKit 2.x (Svelte 5, runes)
- TypeScript
- Tailwind CSS
- Vite 5, Vitest 2
- `@sveltejs/adapter-node` — runs as a Node server in the container
- pnpm (via corepack), Node 20 LTS

## Commands

```bash
pnpm install           # install dependencies (requires corepack-enabled pnpm)
pnpm dev               # dev server on http://localhost:5173
pnpm build             # production build (outputs to ./build)
pnpm preview           # preview the production build locally
pnpm check             # svelte-check (type-check .svelte + .ts)
pnpm lint              # eslint + prettier --check
pnpm format            # prettier --write
pnpm test              # vitest run
pnpm test:watch        # vitest watch
```

## Environment

- `VITE_API_URL` — base URL of the BudgetApp REST API. Defaults to
  `http://localhost:8000/api/v1` in dev. Set at build time for the SPA.

## Docker

The `Dockerfile` produces a two-stage image. The runtime stage runs
`node build` as a non-root user and listens on port 3000. The full stack
is wired up in the repo-root `docker-compose.yml`.
