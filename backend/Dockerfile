FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from backend folder
COPY backend/ .

# Create necessary directories
RUN mkdir -p app/core app/models app/schemas app/services

# Create __init__.py files
RUN touch app/__init__.py && \
    touch app/core/__init__.py && \
    touch app/models/__init__.py && \
    touch app/schemas/__init__.py && \
    touch app/services/__init__.py

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
