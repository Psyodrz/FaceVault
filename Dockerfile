# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies for OpenCV and other ML tasks
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the Cloud Run default port
EXPOSE 8080

# Run the application
# Using 0.0.0.0 to allow external access and 8080 as expected by Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
