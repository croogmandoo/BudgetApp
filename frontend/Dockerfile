# syntax=docker/dockerfile:1.7
# Multi-stage build for the SvelteKit SPA (node adapter).

# ---------- builder ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Enable pnpm via corepack (pinned through the "packageManager" field in package.json).
RUN corepack enable

# Install dependencies first for better layer caching. The wildcard on the
# lockfile lets the initial scaffold build before pnpm-lock.yaml lands; once
# the lockfile is committed, pnpm will respect it automatically. Switch to
# `pnpm install --frozen-lockfile` after the lockfile is in the repo.
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

# Build the app.
COPY . .
RUN pnpm build \
    && pnpm prune --prod

# ---------- runtime ----------
FROM node:20-alpine AS runtime

WORKDIR /app

# Run as a non-root user.
RUN addgroup -S app && adduser -S app -G app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

COPY --from=builder --chown=app:app /app/build ./build
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/package.json ./package.json
COPY --from=builder --chown=app:app /app/pnpm-lock.yaml ./pnpm-lock.yaml

USER app

EXPOSE 3000

CMD ["node", "build"]
