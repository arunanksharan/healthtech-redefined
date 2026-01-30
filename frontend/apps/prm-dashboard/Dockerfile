# Multi-stage Dockerfile for PRM Dashboard
# Optimized for production deployment with Next.js 15

# =============================================================================
# Stage 1: Dependencies
# =============================================================================
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install dependencies based on available lockfile
RUN \
  if [ -f yarn.lock ]; then \
    corepack enable && yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then \
    npm ci --legacy-peer-deps; \
  elif [ -f pnpm-lock.yaml ]; then \
    corepack enable pnpm && pnpm i --frozen-lockfile; \
  else \
    echo "No lockfile found. Running npm install..." && npm install --legacy-peer-deps; \
  fi

# =============================================================================
# Stage 2: Builder
# =============================================================================
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Build-time environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/connect
ARG NEXT_PUBLIC_CONVERSATION_API_URL=http://localhost:3001
ARG NEXT_PUBLIC_CONVERSATION_WS_URL=ws://localhost:3001
ARG NEXT_PUBLIC_LIVEKIT_URL=
ARG NEXT_PUBLIC_ORG_ID=default
ARG NEXT_PUBLIC_TENANT_ID=default
ARG NEXT_PUBLIC_ENABLE_VOICE=true
ARG NEXT_PUBLIC_ENABLE_AI_ASSISTANT=true
ARG NEXT_PUBLIC_ENABLE_AI=true
ARG NEXT_PUBLIC_ENABLE_WHATSAPP=true
ARG NEXT_PUBLIC_ENABLE_SMS=true
ARG NEXT_PUBLIC_ZOICE_API_URL=https://api2.zoice.ai

# Set environment variables
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_CONVERSATION_API_URL=$NEXT_PUBLIC_CONVERSATION_API_URL
ENV NEXT_PUBLIC_CONVERSATION_WS_URL=$NEXT_PUBLIC_CONVERSATION_WS_URL
ENV NEXT_PUBLIC_LIVEKIT_URL=$NEXT_PUBLIC_LIVEKIT_URL
ENV NEXT_PUBLIC_ORG_ID=$NEXT_PUBLIC_ORG_ID
ENV NEXT_PUBLIC_TENANT_ID=$NEXT_PUBLIC_TENANT_ID
ENV NEXT_PUBLIC_ENABLE_VOICE=$NEXT_PUBLIC_ENABLE_VOICE
ENV NEXT_PUBLIC_ENABLE_AI_ASSISTANT=$NEXT_PUBLIC_ENABLE_AI_ASSISTANT
ENV NEXT_PUBLIC_ENABLE_AI=$NEXT_PUBLIC_ENABLE_AI
ENV NEXT_PUBLIC_ENABLE_WHATSAPP=$NEXT_PUBLIC_ENABLE_WHATSAPP
ENV NEXT_PUBLIC_ENABLE_SMS=$NEXT_PUBLIC_ENABLE_SMS
ENV NEXT_PUBLIC_ZOICE_API_URL=$NEXT_PUBLIC_ZOICE_API_URL

# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Enable standalone output for Docker
ENV DOCKER_BUILD=true

# Build application
RUN npm run build

# =============================================================================
# Stage 3: Runner (Production)
# =============================================================================
FROM node:20-alpine AS runner
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install curl for healthcheck
RUN apk add --no-cache curl

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application (standalone mode)
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set port environment variable
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

# Start application
CMD ["node", "server.js"]
