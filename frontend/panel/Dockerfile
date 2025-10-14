FROM node:20-slim

LABEL maintainer="LeviBot Team"
LABEL description="LeviBot Panel - Frontend React App"

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose dev server port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5173 || exit 1

# Run dev server (hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

