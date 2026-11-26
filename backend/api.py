"""API Jangkar Coffee (FastAPI). Semua perhitungan fuzzy dijalankan di Python; frontend hanya menampilkan hasilnya.

Jalankan dari folder backend/:  uvicorn api:app --reload --port 8000
Logikanya ada di layanan.py, dipakai juga oleh wsgi_flask.py (versi WSGI untuk PythonAnywhere).
"""
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import layanan
from layanan import ASAL_CORS, FOLDER_FOTO, MAKS_EXCEL, MAKS_FOTO, GalatLayanan

app = FastAPI(title="Jangkar Coffee API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=ASAL_CORS, allow_methods=["GET", "POST"], allow_headers=["*"])
FOLDER_FOTO.mkdir(parents=True, exist_ok=True)
app.mount("/foto", StaticFiles(directory=FOLDER_FOTO), name="foto")


@app.exception_handler(GalatLayanan)
def _galat(_, e: GalatLayanan):
    return JSONResponse({"detail": e.pesan}, status_code=e.status)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return layanan.ringkasan_meta()


@app.post("/api/rekomendasi")
def rekomendasi(
    lat: Annotated[float, Form()],
    lng: Annotated[float, Form()],
    hemat: Annotated[bool, Form()] = True,
    maks_km: Annotated[float, Form()] = 10,
    kecamatan: Annotated[list[str], Form()] = [],
    jenis: Annotated[list[str], Form()] = [],
    hanya_24: Annotated[bool, Form()] = False,
    limit: Annotated[int, Form()] = 10,
    berkas: Annotated[Optional[UploadFile], File()] = None,
    foto: Annotated[list[UploadFile], File()] = [],
):
    excel = (berkas.filename, berkas.file.read(MAKS_EXCEL + 1)) if berkas is not None and berkas.filename else None
    gambar = [(f.filename, f.content_type, f.file.read(MAKS_FOTO + 1)) for f in foto]
    return layanan.hitung_rekomendasi(lat, lng, hemat, maks_km, kecamatan, jenis, hanya_24, limit, excel, gambar)
