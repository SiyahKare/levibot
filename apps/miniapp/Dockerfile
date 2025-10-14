FROM node:20-alpine

LABEL maintainer="LeviBot Team"
LABEL description="Enterprise AI Signals Platform - Telegram Mini App"

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5173/ || exit 1

# Serve the built app
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]

