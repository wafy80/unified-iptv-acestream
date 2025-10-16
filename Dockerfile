FROM python:3.11-slim

LABEL maintainer="Unified IPTV Platform"
LABEL description="Unified IPTV AceStream Platform with Xtream API"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/data/epg /app/logs /app/config && \
    chmod -R 755 /app/data /app/logs /app/config

# Expose ports
# Note: Dashboard (8000) not exposed - access via SSH tunnel or reverse proxy
EXPOSE 58055 8080 6878

# Health check on unified port
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:58055/health || exit 1

# Run application
CMD ["python", "-u", "main.py"]
