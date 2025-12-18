FROM node:20-alpine AS deps
WORKDIR /app

# Copy only package files for dependency layer caching
COPY package*.json ./
RUN npm ci --only=production --no-audit --prefer-offline

FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./
# Install all dependencies (including dev)
RUN npm ci --no-audit --prefer-offline

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
ENV NODE_OPTIONS=--max-old-space-size=2048

# Build
RUN npm run build

FROM nginx:alpine
WORKDIR /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
