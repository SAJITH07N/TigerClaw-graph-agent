# Multi-stage Python 3.11 Slim Dockerfile for TigerGraph Fraud Agent
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Set working directory
WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications and install Python packages
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy complete application codebase
COPY . .

# Expose API and Web Dashboard port
EXPOSE 8000

# Health check against REST API endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start FastAPI server via Uvicorn
CMD ["python", "-m", "uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
