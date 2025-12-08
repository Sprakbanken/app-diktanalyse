# Use Python 3.13 slim image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Install system deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY src /app/src
COPY README.md ./
COPY pyproject.toml ./

# Install Python dependencies (from pyproject.toml)
RUN uv venv
RUN uv sync --no-dev --compile-bytecode

# Expose port 8501
EXPOSE 8501

# Run the application with Gunicorn (production)
CMD ["uv", "run", "--no-sync", "gunicorn", "--bind", "0.0.0.0:8501", "diktanalyse.app:app"]
