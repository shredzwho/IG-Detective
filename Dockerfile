# Use a slim Debian-based image (Alpine struggles with C-extensions for pandas/scipy/curl_cffi)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies required for compiling extensions (if any) and curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app

# Ensure data directory exists
RUN mkdir -p /app/data

# Run the interactive shell
ENTRYPOINT ["python3", "detective.py"]
