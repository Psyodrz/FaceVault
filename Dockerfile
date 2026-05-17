# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies for OpenCV and other ML tasks
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# API-only on Railway (frontend is deployed on Vercel)
ENV SERVE_FRONTEND=false

EXPOSE 8080

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
