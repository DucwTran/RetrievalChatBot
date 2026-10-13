FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /app

# CPU-only torch first (the default wheel pulls ~2 GB of CUDA libraries).
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY . .

RUN useradd --create-home app \
    && mkdir -p /models /app/logs /app/data \
    && chown -R app:app /models /app/logs /app/data
USER app

EXPOSE 8000

# start-period is long: the embedding and reranker models load before the app is ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status == 200 else 1)"

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
