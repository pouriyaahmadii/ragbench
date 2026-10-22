# RAGBench API - Multi-stage Dockerfile
# Build: docker build --target development -t ragbench-api:dev .
#        docker build --target production -t ragbench-api:prod .

# =============================================================================
# Base Stage - Common dependencies
# =============================================================================
FROM python:3.11-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# System dependencies for PostgreSQL, PDF parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# =============================================================================
# Development Stage - With hot reload
# =============================================================================
FROM base AS development

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml requirements.txt requirements-dev.txt ./

# Install dependencies (dev + production)
RUN uv pip install --system --no-cache -r requirements-dev.txt

# Copy source code
COPY --chown=appuser:appuser . .

USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Production Stage - Optimized
# =============================================================================
FROM base AS production

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install only production dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Copy source code
COPY --chown=appuser:appuser . .

# Run as non-root
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health/ready || exit 1

# Default command (production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]