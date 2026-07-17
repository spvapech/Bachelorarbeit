FROM python:3.13-slim

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/tmp/hf_cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir fastapi uvicorn python-dotenv python-multipart \
    gensim pandas openpyxl supabase statsmodels \
    transformers sentencepiece

COPY backend/ .

RUN mkdir -p models/saved_models

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /tmp
USER appuser

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
