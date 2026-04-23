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

# Build the app. @sveltejs/adapter-node emits a self-contained build/ dir
# that only needs Node at runtime; node_modules stays in the builder stage.
COPY . .
RUN pnpm build

# ---------- runtime ----------
FROM node:20-alpine AS runtime

WORKDIR /app

# Run as a non-root user.
RUN addgroup -S app && adduser -S app -G app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Only the adapter-node output is required at runtime. Leaving node_modules,
# pnpm-lock.yaml, and the pnpm symlink farm out of the final image removes
# the build-tooling surface (esbuild native binary, tar, minimatch, glob,
# cross-spawn, etc.) that Trivy flagged with HIGH/CRITICAL findings.
# package.json is kept so Node picks up "type": "module".
COPY --from=builder --chown=app:app /app/build ./build
COPY --from=builder --chown=app:app /app/package.json ./package.json

USER app

EXPOSE 3000

CMD ["node", "build"]
