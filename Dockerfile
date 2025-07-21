# Dockerfile for dmx
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r dmx && useradd -r -g dmx dmx

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install .

# Copy application code
COPY dmx/ ./dmx/
COPY README.md ./

# Create directories
RUN mkdir -p /app/data /app/logs /app/downloads \
    && chown -R dmx:dmx /app

# Switch to non-root user
USER dmx

# Expose port (if adding web interface later)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD dmx status || exit 1

# Default command
CMD ["dmx"]