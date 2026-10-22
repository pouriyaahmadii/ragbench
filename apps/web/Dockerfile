# RAGBench Web - Multi-stage Dockerfile
# Build: docker build --target development -t ragbench-web:dev .
#        docker build --target production -t ragbench-web:prod .

# =============================================================================
# Base Stage
# =============================================================================
FROM node:20-alpine AS base

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    PNPM_HOME="/pnpm" \
    PATH="/pnpm:${PATH}"

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

# Enable pnpm
RUN corepack enable pnpm

WORKDIR /app

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM base AS deps

COPY package.json pnpm-lock.yaml* package-lock.json* ./

# Install dependencies based on lockfile
RUN if [ -f pnpm-lock.yaml ]; then \
        pnpm install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
        npm ci; \
    else \
        echo "No lockfile found"; exit 1; \
    fi

# =============================================================================
# Development Stage
# =============================================================================
FROM base AS development

COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# =============================================================================
# Builder Stage (Production)
# =============================================================================
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=production
RUN npm run build

# =============================================================================
# Production Stage
# =============================================================================
FROM base AS production

ENV NODE_ENV=production

# Copy standalone output
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]