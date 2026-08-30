# Sovereign AI Workbench — Web (Next.js) image.
# Multi-stage pnpm build for the monorepo. Requires the repository root as the
# Docker build context (see docker-compose.yml) so the pnpm workspace files
# (pnpm-workspace.yaml, pnpm-lock.yaml, root package.json) are available.

# ---- deps: install pnpm + workspace dependencies ----
FROM node:22-alpine AS deps
ENV PNPM_CONFIG_FETCH_TIMEOUT=600000 \
    PNPM_CONFIG_FETCH_RETRIES=5 \
    PNPM_CONFIG_NETWORK_CONCURRENCY=4
RUN npm install -g pnpm@11.21.0
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile --filter @sovereign/web --ignore-scripts

# ---- build: compile the Next.js app ----
FROM deps AS build
WORKDIR /app
COPY . .
RUN pnpm --filter @sovereign/web build

# ---- runtime: only harvest the standalone output ----
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Running as non-root for security.
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs

# Next.js standalone output preserves the monorepo path: apps/web/server.js
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
# Public assets (only if a public dir exists).
COPY --from=build --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
CMD ["node", "apps/web/server.js"]
