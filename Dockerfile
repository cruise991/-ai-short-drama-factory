# Python base image optimized for size
FROM python:3.10-slim

# Install system dependencies (FFmpeg for video/audio processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement list and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code into the container
COPY . /app

# Expose FastAPI backend default port
EXPOSE 8000

# Start the unified entry point in server mode
CMD ["python3", "main.py", "--server"]

