"""Alur data → rekomendasi, tanpa kode UI. Dipakai bersama oleh aplikasi Streamlit dan API FastAPI."""
from urllib.parse import quote_plus

import pandas as pd

from fuzzy_core import RULES, fuzzifikasi, haversine, keanggotaan_harga, label_harga, tsukamoto_tempat

WAJIB = ["nama_maps", "rating", "lat", "lng"]
JENIS_UTAMA = ["Kedai Kopi", "Kafe"]


class DataTidakValid(ValueError):
    """Berkas Excel tidak bisa dipakai (kolom kurang, sheet tidak ada, dsb.)."""


def muat_data(sumber) -> pd.DataFrame:
    """Baca sheet `Data`, lengkapi kolom turunan (jenis, tautan Maps, keanggotaan harga)."""
    try:
        df = pd.read_excel(sumber, sheet_name="Data")
    except ValueError as e:  # sheet tidak ada
        raise DataTidakValid("Sheet 'Data' tidak ditemukan di file Excel.") from e
    kurang = [k for k in WAJIB if k not in df.columns]
    if kurang:
        raise DataTidakValid("Kolom wajib tidak ada di file: " + ", ".join(kurang))
    df = df.dropna(subset=WAJIB).reset_index(drop=True)

    if "kecamatan" not in df:
        df["kecamatan"] = "Tidak diketahui"
    df["kecamatan"] = df["kecamatan"].fillna("Tidak diketahui")
    kategori = df["kategori"] if "kategori" in df else pd.Series("Lainnya", index=df.index)
    df["jenis"] = kategori.where(kategori.isin(JENIS_UTAMA), "Lainnya")
    if "buka_24_jam" not in df:
        df["buka_24_jam"] = "Tidak diketahui"
    if "alamat" not in df:
        df["alamat"] = ""
    df["alamat"] = df["alamat"].fillna("")
    # Kolom link_maps di Excel hanya berisi teks "Buka di Maps". Tautan dibentuk dari nama + alamat
    # supaya Google Maps langsung membuka kafenya, bukan sekadar titik koordinat.
    kueri = (df["nama_maps"].astype(str) + " " + df["alamat"].astype(str)).str.strip()
    df["kueri_maps"] = kueri.map(quote_plus)
    df["link_maps"] = "https://www.google.com/maps/search/?api=1&query=" + df["kueri_maps"]

    # Template hasil scraping tidak punya kolom keanggotaan harga: hitung dari rentang harga.
    ada_harga = "harga_min" in df and "harga_max" in df
    ada_mu = {"mu_murah", "mu_sedang", "mu_mahal"} <= set(df.columns)
    if not ada_mu:
        if not ada_harga:
            raise DataTidakValid("Kolom harga_min dan harga_max (atau mu_murah, mu_sedang, mu_mahal) tidak ada.")
        mu = [keanggotaan_harga(a, b) for a, b in zip(df["harga_min"], df["harga_max"])]
        df["mu_murah"], df["mu_sedang"], df["mu_mahal"] = zip(*mu) if mu else ([], [], [])
    if "harga_label" not in df:
        df["harga_label"] = (
            [label_harga(a, b) for a, b in zip(df["harga_min"], df["harga_max"])] if ada_harga else ""
        )
    return df


def hitung(df: pd.DataFrame, lat: float, lng: float, hemat: bool) -> pd.DataFrame:
    """Tambah kolom jarak_km dan skor (z akhir Tsukamoto, 0–100)."""
    df = df.copy()
    df["jarak_km"] = [haversine(lat, lng, a, b) for a, b in zip(df["lat"], df["lng"])]
    df["skor"] = [
        tsukamoto_tempat(r.jarak_km, r.rating, r.mu_murah, r.mu_sedang, r.mu_mahal, hemat)[0]
        for r in df.itertuples()
    ]
    return df


def saring(df: pd.DataFrame, maks_km=None, kecamatan=(), jenis=(), hanya_24=False) -> pd.DataFrame:
    """Filter tegas (crisp), lalu urutkan dari skor tertinggi."""
    if maks_km is not None:
        df = df[df["jarak_km"] <= maks_km]
    if kecamatan:
        df = df[df["kecamatan"].isin(kecamatan)]
    if jenis:
        df = df[df["jenis"].isin(jenis)]
    if hanya_24:
        df = df[df["buka_24_jam"] == "Ya"]
    return df.sort_values("skor", ascending=False)


def link_rute(lat: float, lng: float, kueri_maps: str) -> str:
    return f"https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={kueri_maps}&travelmode=driving"


def rincian(baris, hemat: bool) -> dict:
    """Langkah-langkah perhitungan fuzzy satu kafe: fuzzifikasi, tiap aturan, z akhir."""
    z, zs = tsukamoto_tempat(baris.jarak_km, baris.rating, baris.mu_murah, baris.mu_sedang, baris.mu_mahal, hemat)
    return {
        "fuzzifikasi": {
            **fuzzifikasi(baris.jarak_km, baris.rating),
            "murah": float(baris.mu_murah),
            "sedang": float(baris.mu_sedang),
            "mahal": float(baris.mu_mahal),
        },
        "aturan": [
            {"aturan": nama, "alpha": a, "z": zi, "alpha_z": a * zi} for nama, (a, zi) in zip(RULES, zs)
        ],
        "z_akhir": z,
    }
