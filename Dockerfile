# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first so they're cached across code-only changes
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files (.dockerignore keeps secrets/.git/raw data out of the image)
COPY . .

RUN useradd --create-home --uid 1000 kara \
    && mkdir -p logs dagster_home \
    && chown -R kara:kara /app
USER kara

# Default command can be overridden in docker-compose
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
