# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main_api.py .
COPY gradio_app.py .
COPY start.sh .
COPY .env* ./

# Make startup script executable
RUN chmod +x start.sh

# Expose ports
# 8080 for FastAPI backend
# 7860 for Gradio frontend
EXPOSE 8080
EXPOSE 7860

# Set environment variables
ENV PORT=8080
ENV GRADIO_PORT=7860
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start both services using the startup script
CMD ["./start.sh"]
