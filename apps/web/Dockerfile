# Multi-stage Dockerfile for Next.js application
# Stage 1: Base image with Node.js
FROM node:18-alpine AS base

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Install dependencies only when needed
FROM base AS deps

# Copy package files
COPY package.json package-lock.json* ./
COPY ../../packages ./packages

# Install dependencies
RUN npm install --only=production && npm cache clean --force

# Development stage
FROM base AS development

# Set environment variables
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Install all dependencies (including devDependencies)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Create .next directory and set proper permissions
RUN mkdir -p /app/.next && chown -R node:node /app

# Expose port
EXPOSE 3000

# Set user
USER node

# Start development server
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS builder

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy package files and install all dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM base AS production

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create app user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set correct permissions
RUN chown -R nextjs:nodejs /app

# Switch to app user
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start production server
CMD ["node", "server.js"]