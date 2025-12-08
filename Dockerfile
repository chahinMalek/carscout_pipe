# syntax=docker/dockerfile:1

# Build stage using uv for fast dependency installation
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY .python-version ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies if needed (e.g., for selenium/scrapy)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY core/ ./core/
COPY infra/ ./infra/
COPY scripts/ ./scripts/
COPY tasks/ ./tasks/
COPY data/ ./data/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "-m", "app.cli"]
