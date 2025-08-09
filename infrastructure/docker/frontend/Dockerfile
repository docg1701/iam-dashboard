# Frontend Dockerfile for Multi-Agent IAM Dashboard
FROM node:20-alpine AS base

# Install dependencies for building native modules
RUN apk add --no-cache libc6-compat curl

# Set working directory
WORKDIR /app

# Copy root package files for workspace
COPY package.json package-lock.json* ./
COPY packages/ ./packages/

# Copy frontend package file
COPY apps/frontend/package.json ./apps/frontend/

# Install dependencies (both root and frontend)
RUN npm ci --workspace=apps/frontend --include-workspace-root || npm install --workspace=apps/frontend --include-workspace-root

# Copy frontend source code
COPY apps/frontend/ ./apps/frontend/

# Build application
WORKDIR /app/apps/frontend
RUN npm run build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start application
CMD ["npm", "start"]