# Multi-stage build for Next.js application
# Stage 1: Builder - Install dependencies and build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies with retry logic for network issues
RUN npm install --legacy-peer-deps 2>&1 | tail -20

# Copy application code
COPY . .

# Set environment for build with increased memory and public API url (can be overridden at build time)
ARG NEXT_PUBLIC_API_URL=/api
ENV NODE_OPTIONS=--max-old-space-size=2048 NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build Next.js application
RUN npm run build

# Stage 2: Production - Run the built application
FROM node:20-alpine

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm install --legacy-peer-deps --omit=dev 2>&1 | tail -10

# Propagate public API URL to runtime (overridable)
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

USER nextjs

# Expose port
EXPOSE 3000

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start Next.js server
CMD ["npm", "start"]
