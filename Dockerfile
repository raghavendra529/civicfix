# CivicFix Docker Production Container
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure upload directory exists
RUN mkdir -p backend/uploads

# Expose port
EXPOSE 5000

# Run with Gunicorn WSGI
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "wsgi:app"]
