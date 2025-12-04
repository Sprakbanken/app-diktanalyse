# Use Python 3.13 slim image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app
        
# Install system deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from pyproject.toml)
COPY pyproject.toml ./
RUN uv venv
RUN uv pip install -r pyproject.toml

# Copy application code
COPY app.py tasks.py config.py ./
COPY templates ./templates/
COPY static/poems.json ./static/poems.json

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV GUNICORN_WORKERS=4

# Expose port 5000
EXPOSE $PORT

# Run the application with Gunicorn (production)
# Use env vars PORT and GUNICORN_WORKERS to configure
CMD ["bash", "-c", "uv run gunicorn -w ${GUNICORN_WORKERS} -b 0.0.0.0:${PORT} app:app"]
