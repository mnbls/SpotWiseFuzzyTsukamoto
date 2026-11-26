"""Logika API tanpa kerangka web: dipakai bersama oleh api.py (FastAPI, lokal) dan wsgi_flask.py (Flask, PythonAnywhere).

Semua perhitungan fuzzy tetap di rekomendasi.py dan fuzzy_core.py.
"""
import base64
import io
import os
from functools import lru_cache
from pathlib import Path

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
JENIS = ["Kedai Kopi", "Kafe", "Lainnya"]

# CORS_ORIGINS="https://situs-kamu.github.io,http://localhost:5174" untuk membatasi; bawaan: semua asal (tanpa cookie).
ASAL_CORS = [a.strip() for a in os.getenv("CORS_ORIGINS", "*").split(",") if a.strip()]


class GalatLayanan(Exception):
    """Galat yang dikirim ke klien sebagai {"detail": pesan} dengan kode HTTP `status`."""

    def __init__(self, status: int, pesan: str):
        super().__init__(pesan)
        self.status = status
        self.pesan = pesan


@lru_cache(maxsize=1)
def data_bawaan():
    berkas = next((b for b in BERKAS_BAWAAN if b.is_file()), None)
    if berkas is None:
        return None, None
    return berkas.name, muat_data(berkas)


def ambil_data(berkas):
    """`berkas` = (nama, isi bytes) dari unggahan, atau None untuk data bawaan."""
    if berkas is not None and berkas[0]:
        nama, isi = berkas
        if len(isi) > MAKS_EXCEL:
            raise GalatLayanan(413, "File Excel terlalu besar (maksimal 10 MB).")
        try:
            return nama, muat_data(io.BytesIO(isi))
        except DataTidakValid as e:
            raise GalatLayanan(400, str(e)) from e
        except Exception as e:  # file rusak / bukan xlsx
            raise GalatLayanan(400, "File tidak bisa dibaca. Pastikan formatnya .xlsx.") from e
    nama, df = data_bawaan()
    if df is None:
        raise GalatLayanan(404, "Belum ada data. Unggah file Excel hasil scraping.")
    return nama, df


def foto_unggahan(daftar) -> dict:
    """`daftar` = [(nama, tipe, isi bytes)] → {nama: data-URI}. Yang bukan gambar atau terlalu besar dilewati."""
    hasil = {}
    for nama, tipe, isi in daftar[:MAKS_JUMLAH_FOTO]:
        if not nama or tipe not in TIPE_FOTO or len(isi) > MAKS_FOTO:
            continue
        hasil[nama] = f"data:{tipe};base64," + base64.b64encode(isi).decode()
    return hasil


def url_foto(nama, unggahan: dict):
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


def ringkasan_meta() -> dict:
    """Ringkasan data bawaan: untuk mengisi pilihan filter dan titik awal peta."""
    nama, df = data_bawaan()
    if df is None:
        return {"tersedia": False, "sumber": None, "jumlah": 0, "kecamatan": [], "jenis": [], "pusat": None}
    return {
        "tersedia": True,
        "sumber": nama,
        "jumlah": int(len(df)),
        "kecamatan": sorted(df["kecamatan"].unique().tolist()),
        "jenis": JENIS,
        "pusat": {"lat": float(df["lat"].mean()), "lng": float(df["lng"].mean())},
    }


def periksa_masukan(lat, lng, maks_km, limit):
    """Batas yang sama untuk FastAPI dan Flask."""
    if not -90 <= lat <= 90:
        raise GalatLayanan(422, "Input tidak valid: lat harus antara -90 dan 90.")
    if not -180 <= lng <= 180:
        raise GalatLayanan(422, "Input tidak valid: lng harus antara -180 dan 180.")
    if not 0 < maks_km <= 500:
        raise GalatLayanan(422, "Input tidak valid: maks_km harus lebih dari 0 dan paling besar 500.")
    if not 1 <= limit <= MAKS_HASIL:
        raise GalatLayanan(422, f"Input tidak valid: limit harus 1 sampai {MAKS_HASIL}.")


def hitung_rekomendasi(lat, lng, hemat=True, maks_km=10, kecamatan=(), jenis=(), hanya_24=False, limit=10,
                       berkas=None, foto=()) -> dict:
    """Hitung skor fuzzy Tsukamoto tiap kafe dari lokasi pengguna, lalu kembalikan yang terbaik."""
    periksa_masukan(lat, lng, maks_km, limit)
    sumber, df = ambil_data(berkas)
    unggahan = foto_unggahan(list(foto))
    df = hitung(df, lat, lng, hemat)
    terpilih = saring(df, maks_km, list(kecamatan), list(jenis), hanya_24)

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
            "foto": url_foto(getattr(r, "foto", None), unggahan),
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
