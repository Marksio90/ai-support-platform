FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install minimal dependencies for service
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.3 \
    sentence-transformers==2.2.2 \
    faiss-cpu==1.7.4 \
    numpy==1.24.3

# Copy service code and utilities
COPY service.py .
COPY chunker.py .
COPY retriever.py .

# Create vectorstore directory
RUN mkdir -p vectorstore

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')"

# Run service
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8002"]
