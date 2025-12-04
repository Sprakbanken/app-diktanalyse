# Use Python 3.13 slim image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app
        
# Install system deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from pyproject.toml)
RUN uv venv
RUN uv pip install \
	flask>=3.1.2 \
	poetree>=0.0.2 \
	poetry-analysis>=0.3.14 \
	python-dotenv>=1.2.1 \
	requests>=2.32.0 \
	gunicorn>=23.0.0

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
