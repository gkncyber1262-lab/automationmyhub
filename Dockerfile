FROM python:3.11-slim

# Install system dependencies including LibreOffice for headless DOCX to PDF conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-core \
    fonts-dejavu \
    fonts-freefont-ttf \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set default port for Koyeb / Cloud
ENV PORT=8000
EXPOSE 8000

# Start 24/7 Unified Cloud Service Runner (FastAPI Health Check + Telegram Bot)
CMD ["python", "run_cloud_service.py"]
