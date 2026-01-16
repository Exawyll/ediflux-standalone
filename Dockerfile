FROM python:3.9-slim

# Install dependencies
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
# Default to LOCAL storage, override at runtime in Cloud Run with 'GCS' and 'GCS_BUCKET_NAME'
ENV STORAGE_TYPE=LOCAL
ENV PORT=8080

# Run the web service on container startup.
# Cloud Run expects the app to listen on $PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
