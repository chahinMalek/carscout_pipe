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
COPY uv.lock ./
COPY README.md ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY core/ ./core/
COPY infra/ ./infra/
COPY scripts/ ./scripts/
COPY worker/ ./worker/
COPY resources/ ./resources/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "-m", "app.cli"]
