# Jangkar Coffee

Sistem pendukung keputusan (SPK) yang merekomendasikan **kafe terbaik** dari data Google Maps dengan metode **Fuzzy Tsukamoto**.
Seluruh perhitungan (jarak, keanggotaan fuzzy, inferensi, defuzzifikasi) ditulis dengan **Python**. Web React hanya menampilkan hasilnya.

```
Data kafe (scraping Google Maps → .xlsx + foto)
        │
        ▼
 Backend Python (FastAPI): baca data → jarak (Haversine) → fuzzifikasi → 5 aturan IF-THEN → defuzzifikasi
        │  JSON
        ▼
 Web React: carousel kartu foto yang bisa digeser, tabel, peta, rincian perhitungan
```

## Struktur

```
.
├── backend/                 Python
│   ├── fuzzy_core.py        inti fuzzy (tanpa dependensi UI): Haversine, keanggotaan harga, Tsukamoto
│   ├── rekomendasi.py       alur data → skor: baca Excel, hitung, saring, rincian perhitungan
│   ├── layanan.py           logika API tanpa kerangka web (validasi, unggahan, bentuk JSON)
│   ├── api.py               API FastAPI untuk lokal (memakai layanan.py)
│   ├── wsgi_flask.py        API yang sama dalam Flask (WSGI murni) untuk PythonAnywhere
│   ├── app.py               aplikasi Streamlit lama (cadangan, memakai rekomendasi.py yang sama)
│   ├── carousel.py, tabel.py, logo.svg, .streamlit/   khusus aplikasi Streamlit
│   ├── requirements-api.txt dependensi API saja; requirements.txt = API + Streamlit; requirements-dev.txt = tes
│   ├── Dockerfile           image API untuk layanan berbasis Docker (Fly.io, Render, dsb.)
│   ├── data/                satu Excel contoh dan foto hasil scraping (ikut git, lihat data/README.md)
│   └── tests/               tes unit: fuzzy_core dan API
├── frontend/                Web: Vite + React 19 + TypeScript + Tailwind v4
│   └── src/
│       ├── components/ui/   syntra-hero.tsx (hero beranda)
│       ├── components/app/  CarouselKafe, TabelHasil, PetaKafe, RincianFuzzy, FormPreferensi
│       ├── pages/           AplikasiPage.tsx
│       ├── lib/api.ts       klien API
│       └── demo.tsx         pengatur halaman: #/ beranda, #/app aplikasi
├── docs/
│   ├── METODE.md            rumus dan aturan fuzzy secara rinci
│   └── PROGRESS.md          status pekerjaan dan keputusan
├── render.yaml              blueprint Render untuk backend
└── .github/workflows/       deploy web ke GitHub Pages
```

## Menjalankan di lokal

Butuh Python 3.11+ dan Node 22+. Buka dua terminal.

**1. Backend Python** (http://localhost:8000):

```powershell
cd backend
pip install -r requirements.txt
uvicorn api:app --port 8000
```

**2. Web** (http://localhost:5174):

```powershell
cd frontend
npm install
npm run dev
```

Buka http://localhost:5174, lalu klik **Mulai**. Halaman aplikasi ada di `#/app`.
Bila API tidak di `localhost:8000`, set `VITE_API_URL` (mis. `$env:VITE_API_URL = "https://api-kamu.example.com"`) sebelum `npm run dev` atau `npm run build`.

**Tes Python:**

```powershell
cd backend
pip install -r requirements-dev.txt
python -m unittest discover tests
```

**Build web:** `cd frontend; npm run build` (hasilnya di `frontend/dist`).

**Aplikasi Streamlit lama** (opsional): `cd backend; streamlit run app.py`.

## API

| Endpoint | Fungsi |
|---|---|
| `GET /api/health` | cek server hidup |
| `GET /api/meta` | ringkasan data bawaan: sumber, jumlah, kecamatan, titik tengah |
| `POST /api/rekomendasi` | hitung skor tiap kafe dari lokasi pengguna, kembalikan yang terbaik |
| `GET /foto/<nama>` | foto dari `backend/data/foto/` |

`POST /api/rekomendasi` menerima `multipart/form-data`:
`lat`, `lng` (wajib), `hemat` (true/false), `maks_km`, `kecamatan` (boleh berulang), `jenis` (boleh berulang), `hanya_24`, `limit` (1–30),
serta `berkas` (Excel, opsional) dan `foto` (gambar, boleh banyak). Tanpa `berkas`, dipakai data bawaan di `backend/data/`.
Balasannya berisi daftar kafe terurut lengkap dengan skor, tautan Maps dan rute, serta rincian perhitungan tiap aturan.
Dokumentasi interaktif otomatis ada di http://localhost:8000/docs.

Batas unggahan: Excel 10 MB, foto 5 MB per berkas (maksimal 40).
Variabel lingkungan: `CORS_ORIGINS` (asal yang boleh memanggil API, pisahkan dengan koma; bawaannya semua asal) dan `DATA_DIR` (folder data bawaan; bawaannya `backend/data`).

## Data

Aplikasi membaca file Excel hasil scraping (sheet `Data`) dari `backend/data/` atau dari unggahan.
Kolom wajib: `nama_maps, rating, lat, lng`. Kolom `foto` berisi nama file gambar di `backend/data/foto/`.
Rincian kolom ada di [backend/data/README.md](backend/data/README.md).

## Metode singkat

Tiga masukan fuzzy: **jarak** (dekat/jauh), **rating** (tinggi/rendah), dan **harga** (murah/sedang/mahal).
Lima aturan IF-THEN, operator AND = min, skor akhir z = Σ(α·z) / Σα, dengan nilai 0–100.
Mode **Hemat** menjadikan harga mahal berdampak rendah, mode **Bebas** menjadikannya tinggi.
Rumus lengkap: [docs/METODE.md](docs/METODE.md).

## Deploy

- **Web:** GitHub Pages lewat GitHub Actions. Di pengaturan repo, **Pages → Source** harus **GitHub Actions**.
  Isi variabel repo `API_URL` (Settings → Secrets and variables → Actions → Variables) dengan alamat backend; nilainya dipakai saat build sebagai `VITE_API_URL`.
- **Backend (yang dipakai): PythonAnywhere** di https://mnbls.pythonanywhere.com, gratis tanpa kartu kredit.
  Server web PythonAnywhere tidak menjalankan thread Python, jadi FastAPI (lewat adapter ASGI→WSGI) macet di sana.
  Karena itu dipakai `wsgi_flask.py`: endpoint dan bentuk JSON-nya sama dengan `api.py`, logikanya sama-sama dari `layanan.py`.
  1. Daftar akun Beginner di https://www.pythonanywhere.com/registration/register/beginner/
  2. **Consoles → Bash**:
     ```bash
     git clone https://github.com/mnbls/SpotWiseFuzzyTsukamoto.git jangkar
     python3.11 -m pip install --user flask pandas openpyxl
     ```
  3. **Web → Add a new web app → Next → Manual configuration → Python 3.11 → Next.**
  4. Ganti seluruh isi **WSGI configuration file** (`/var/www/<username>_pythonanywhere_com_wsgi.py`) dengan:
     ```python
     import sys
     sys.path.insert(0, "/home/mnbls/jangkar/backend")
     from wsgi_flask import app as application  # noqa: E402,F401
     ```
  5. Klik **Reload** di tab Web, lalu cek `https://mnbls.pythonanywhere.com/api/health`.
  6. Memperbarui kode: di Bash console `cd ~/jangkar && git pull`, lalu **Reload**.

  Akun gratis harus diperpanjang dengan tombol **Run until 3 months from today** di tab Web, kalau tidak web app dimatikan.
  Error saat jalan terlihat di **Error log** di tab Web.
- **Backend (alternatif berbayar atau butuh kartu):** Render memakai `render.yaml`; layanan berbasis Docker memakai `backend/Dockerfile`.
  Hugging Face Spaces kini mewajibkan paket berbayar untuk Space Docker. Cara umum lainnya: dari folder `backend/`, `pip install -r requirements-api.txt`, lalu `uvicorn api:app --host 0.0.0.0 --port $PORT`.

  Set `CORS_ORIGINS` ke alamat web (mis. `https://mnbls.github.io`), lalu isi variabel repo `API_URL` dengan alamat backend dan jalankan ulang workflow web.
  Versi Flask diuji di lokal dengan server WSGI satu-thread; `render.yaml` dan `Dockerfile` belum pernah dijalankan di layanannya.
- **Data di server:** `backend/data/coffee-depok-sleman.xlsx` dan `backend/data/foto/` ikut git, jadi server langsung berisi data contoh.
  Untuk data lain, ganti berkas itu, atau arahkan `DATA_DIR` ke folder yang berisi Excel dan subfolder `foto/`. Tanpa data bawaan, web meminta pengguna mengunggah Excel.

Status dan rencana: [docs/PROGRESS.md](docs/PROGRESS.md).
