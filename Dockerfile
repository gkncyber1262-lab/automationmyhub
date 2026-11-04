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

# Set default port
ENV PORT=5005
EXPOSE 5005

# Start WhatsApp webhook service
CMD ["python", "NCRP_Master_Agent/whatsapp_webhook_service.py"]
