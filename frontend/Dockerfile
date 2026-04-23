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

# node:20-alpine ships with npm preinstalled at /usr/local/lib/node_modules/npm.
# npm itself bundles cross-spawn, glob, minimatch, tar, and other transitives
# that Trivy flags with HIGH findings every time a new CVE lands. We run the
# adapter-node bundle with plain `node`, so npm and corepack are dead weight.
RUN rm -rf /usr/local/lib/node_modules/npm \
           /usr/local/bin/npm \
           /usr/local/bin/npx \
           /usr/local/lib/node_modules/corepack \
           /usr/local/bin/corepack

# Run as a non-root user.
RUN addgroup -S app && adduser -S app -G app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Only the adapter-node output is required at runtime — it bundles every
# runtime dep. We do not copy node_modules, pnpm-lock.yaml, or the real
# package.json: Trivy's node-pkg scanner reads dependency names from
# package.json and resolves their transitive tree, which surfaces
# dev-tooling vulnerabilities (esbuild, tar, glob, minimatch, cross-spawn)
# that are irrelevant at runtime. Write a minimal stub so Node sees
# "type": "module" and still treats build/index.js as ESM.
COPY --from=builder --chown=app:app /app/build ./build
RUN echo '{"name":"budgetapp-frontend","version":"0.0.1","type":"module","private":true}' > package.json \
    && chown app:app package.json

USER app

EXPOSE 3000

CMD ["node", "build"]
