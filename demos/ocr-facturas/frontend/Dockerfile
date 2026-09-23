# ============================================================================
# OCR Facturas — Frontend Dockerfile
# Multi-stage build: build (Vite/React) → nginx (serve static files)
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build — compile React application with Vite
# ---------------------------------------------------------------------------
FROM node:20-slim AS build

WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the React application (output goes to /app/dist)
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Nginx — serve compiled static files with nginx
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled React app from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check — verify nginx is serving content
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Use nginx foreground mode (default CMD from nginx image)
CMD ["nginx", "-g", "daemon off;"]