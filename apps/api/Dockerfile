# Sovereign AI Workbench — API (FastAPI) image.
# Requires the repository root as the Docker build context (see docker-compose.yml).
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Local OCR engine (RapidOCR, ONNX). OCR is always local — never a cloud service.
RUN pip install --no-cache-dir rapidocr-onnxruntime

# Copy only the API package (context is the repo root).
COPY apps/api/ ./api
WORKDIR /app/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
