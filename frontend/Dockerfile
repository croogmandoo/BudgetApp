# syntax=docker/dockerfile:1.7
# Multi-stage build for the SvelteKit SPA (node adapter).

# ---------- deps: production-only node_modules ----------
# Separate stage so the runtime image gets a lean, dev-free node_modules
# without having to install everything twice in one stage.
FROM node:22-alpine AS deps

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod

# ---------- builder ----------
FROM node:22-alpine AS builder

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

# ---------- runtime ----------
FROM node:22-alpine AS runtime

WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# adapter-node output imports from @sveltejs/kit and other runtime deps at
# startup — it is NOT a fully self-contained bundle. Copy the production
# node_modules from the deps stage alongside the build output.
COPY --from=deps    --chown=app:app /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/build        ./build
COPY --from=deps    --chown=app:app /app/package.json ./package.json

USER app

EXPOSE 3000

CMD ["node", "build"]
