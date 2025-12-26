FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Copy service code
COPY service.py .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run service
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8001"]
