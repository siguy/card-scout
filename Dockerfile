# Use a lightweight python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies directly
RUN pip install --no-cache-dir \
    pydantic==2.12.5 \
    fastapi==0.128.0 \
    uvicorn==0.48.0 \
    google-antigravity==0.1.0

# Copy application files
COPY backend/ /app/backend/

# Expose target Cloud Run port
EXPOSE 8080

# Command to execute FastAPI server
CMD ["python", "backend/server.py"]
