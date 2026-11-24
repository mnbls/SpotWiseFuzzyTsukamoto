"""API Jangkar Coffee. Semua perhitungan fuzzy dijalankan di Python (fuzzy_core.py); frontend hanya menampilkan hasilnya.

Jalankan dari folder backend/:  uvicorn api:app --reload --port 8000
"""
import base64
import io
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rekomendasi import DataTidakValid, hitung, link_rute, muat_data, rincian, saring

BASE = Path(__file__).parent
FOLDER_DATA = Path(os.getenv("DATA_DIR", BASE / "data"))  # DATA_DIR: mis. disk persisten di server
FOLDER_FOTO = FOLDER_DATA / "foto"
BERKAS_BAWAAN = [FOLDER_DATA / "coffee-depok-sleman.xlsx", FOLDER_DATA / "coffee-sleman-harga.xlsx"]

MAKS_EXCEL = 10 * 1024 * 1024
MAKS_FOTO = 5 * 1024 * 1024
MAKS_JUMLAH_FOTO = 40
MAKS_HASIL = 30
TIPE_FOTO = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Jangkar Coffee API", version="1.0.0")
# CORS_ORIGINS="https://situs-kamu.github.io,http://localhost:5174" untuk membatasi; bawaan: semua asal (tanpa cookie).
_asal = [a.strip() for a in os.getenv("CORS_ORIGINS", "*").split(",") if a.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_asal, allow_methods=["GET", "POST"], allow_headers=["*"])
FOLDER_FOTO.mkdir(parents=True, exist_ok=True)
app.mount("/foto", StaticFiles(directory=FOLDER_FOTO), name="foto")


@lru_cache(maxsize=1)
def _data_bawaan():
    berkas = next((b for b in BERKAS_BAWAAN if b.is_file()), None)
    if berkas is None:
        return None, None
    return berkas.name, muat_data(berkas)


def _ambil_data(berkas: Optional[UploadFile]):
    """Data dari upload bila ada, selain itu berkas bawaan di backend/data/."""
    if berkas is not None and berkas.filename:
        isi = berkas.file.read(MAKS_EXCEL + 1)
        if len(isi) > MAKS_EXCEL:
            raise HTTPException(413, "File Excel terlalu besar (maksimal 10 MB).")
        try:
            return berkas.filename, muat_data(io.BytesIO(isi))
        except DataTidakValid as e:
            raise HTTPException(400, str(e)) from e
        except Exception as e:  # file rusak / bukan xlsx
            raise HTTPException(400, "File tidak bisa dibaca. Pastikan formatnya .xlsx.") from e
    nama, df = _data_bawaan()
    if df is None:
        raise HTTPException(404, "Belum ada data. Unggah file Excel hasil scraping.")
    return nama, df


def _foto_unggahan(daftar: list[UploadFile]) -> dict[str, str]:
    """Foto yang diunggah → data-URI, dikunci dengan nama file."""
    hasil = {}
    for f in daftar[:MAKS_JUMLAH_FOTO]:
        if not f.filename or f.content_type not in TIPE_FOTO:
            continue
        isi = f.file.read(MAKS_FOTO + 1)
        if len(isi) > MAKS_FOTO:
            continue
        hasil[f.filename] = f"data:{f.content_type};base64," + base64.b64encode(isi).decode()
    return hasil


def _url_foto(nama, unggahan: dict[str, str]):
    if not isinstance(nama, str) or not nama.strip():
        return None
    nama = nama.strip()
    if nama.startswith(("http://", "https://")):
        return nama
    if nama in unggahan:
        return unggahan[nama]
    return f"/foto/{nama}" if (FOLDER_FOTO / nama).is_file() else None


def _bulat(v):
    return None if v is None or v != v else int(v)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    """Ringkasan data bawaan: untuk mengisi pilihan filter dan titik awal peta."""
    nama, df = _data_bawaan()
    if df is None:
        return {"tersedia": False, "sumber": None, "jumlah": 0, "kecamatan": [], "jenis": [], "pusat": None}
    return {
        "tersedia": True,
        "sumber": nama,
        "jumlah": int(len(df)),
        "kecamatan": sorted(df["kecamatan"].unique().tolist()),
        "jenis": ["Kedai Kopi", "Kafe", "Lainnya"],
        "pusat": {"lat": float(df["lat"].mean()), "lng": float(df["lng"].mean())},
    }


@app.post("/api/rekomendasi")
def rekomendasi(
    lat: Annotated[float, Form(ge=-90, le=90)],
    lng: Annotated[float, Form(ge=-180, le=180)],
    hemat: Annotated[bool, Form()] = True,
    maks_km: Annotated[float, Form(gt=0, le=500)] = 10,
    kecamatan: Annotated[list[str], Form()] = [],
    jenis: Annotated[list[str], Form()] = [],
    hanya_24: Annotated[bool, Form()] = False,
    limit: Annotated[int, Form(ge=1, le=MAKS_HASIL)] = 10,
    berkas: Annotated[Optional[UploadFile], File()] = None,
    foto: Annotated[list[UploadFile], File()] = [],
):
    """Hitung skor fuzzy Tsukamoto tiap kafe dari lokasi pengguna, lalu kembalikan yang terbaik."""
    sumber, df = _ambil_data(berkas)
    unggahan = _foto_unggahan(foto)
    df = hitung(df, lat, lng, hemat)
    terpilih = saring(df, maks_km, kecamatan, jenis, hanya_24)

    hasil = []
    for urut, r in enumerate(terpilih.head(limit).itertuples(), start=1):
        hasil.append({
            "peringkat": urut,
            "nama": r.nama_maps,
            "jenis": r.jenis,
            "kecamatan": r.kecamatan,
            "alamat": r.alamat,
            "harga": r.harga_label,
            "rating": float(r.rating),
            "jumlah_ulasan": _bulat(getattr(r, "jumlah_ulasan", None)),
            "buka_24_jam": r.buka_24_jam == "Ya",
            "jarak_km": float(r.jarak_km),
            "skor": float(r.skor),
            "lat": float(r.lat),
            "lng": float(r.lng),
            "foto": _url_foto(getattr(r, "foto", None), unggahan),
            "maps": r.link_maps,
            "rute": link_rute(lat, lng, r.kueri_maps),
            "perhitungan": rincian(r, hemat),
        })
    return {
        "sumber": sumber,
        "mode": "Hemat" if hemat else "Bebas",
        "total_data": int(len(df)),
        "jumlah": int(len(terpilih)),
        "kecamatan_tersedia": sorted(df["kecamatan"].unique().tolist()),
        "hasil": hasil,
        "peta": [
            {"nama": r.nama_maps, "lat": float(r.lat), "lng": float(r.lng)}
            for r in terpilih.head(300).itertuples()
        ],
    }
