# Image untuk API Jangkar Coffee (Render, Hugging Face Spaces, Fly.io, dsb.).
FROM python:3.12-slim

WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY fuzzy_core.py rekomendasi.py layanan.py api.py wsgi_flask.py ./
# Data bawaan (opsional). Tanpa folder data, web meminta pengguna mengunggah Excel.
COPY data ./data

# PORT diisi platform (Render: 10000, Hugging Face Spaces: 7860).
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
