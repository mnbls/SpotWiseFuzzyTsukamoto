# Status pekerjaan

Cara menjalankan dan gambaran proyek ada di [README](../README.md); rumus ada di [METODE.md](METODE.md).

## Sudah ada

- [x] Beranda (Vite + React): hero 3D yang menjelaskan alur kerja, tombol **Mulai** membuka halaman aplikasi (`#/app`)
- [x] Halaman aplikasi React: upload Excel dan foto, lokasi (ketik, lokasi saya, klik peta), mode harga Hemat/Bebas, filter, carousel kartu foto yang bisa digeser, tabel yang bisa diurut, peta, rincian perhitungan fuzzy
- [x] API FastAPI (`backend/api.py`): semua hitungan lewat Python; tes API dan tes inti fuzzy (20 tes)
- [x] Inti fuzzy Tsukamoto di `backend/fuzzy_core.py`; alur data di `backend/rekomendasi.py` dipakai bersama oleh API dan Streamlit
- [x] Template data baru dari scraping (kolom `foto`, tanpa `mu_*`); keanggotaan harga dihitung di Python
- [x] Struktur proyek dibagi `backend/`, `frontend/`, `docs/`
- [x] Aplikasi Streamlit lama tetap ada sebagai cadangan (`backend/app.py`)
- [x] Tabel di web: urut per kolom dan lebar kolom bisa ditarik (klik dua kali untuk mengembalikan)
- [x] Logo jangkar yang menjulang dari cangkir kopi (`frontend/public/favicon.svg`, `backend/logo.svg`, dan navbar beranda)
- [x] Web menampilkan ajakan unggah bila server belum punya data bawaan
- [x] Berkas deploy backend: `render.yaml`, `backend/Dockerfile`, `backend/requirements-api.txt`, variabel `DATA_DIR`

## Belum

- [ ] Isi variabel repo `API_URL` dengan `https://mnbls.pythonanywhere.com` dan jalankan ulang workflow web
- [ ] Perpanjang web app PythonAnywhere tiap 3 bulan (tombol di tab Web)
- [ ] Ganti nama repo dari `SpotWiseFuzzyTsukamoto` ke nama baru
- [ ] Hapus `backend/app.py` dan berkas Streamlit bila versi web sudah dipakai penuh

## Keputusan

- **Hosting backend:** PythonAnywhere (gratis, tanpa kartu kredit) dengan `wsgi_flask.py`. Render minta kartu, Hugging Face Spaces kini mewajibkan paket berbayar untuk Space Docker, dan FastAPI lewat adapter `a2wsgi` macet di PythonAnywhere karena server webnya tidak menjalankan thread. Logika API ada di `layanan.py` sehingga FastAPI (lokal) dan Flask (server) membalas sama; tes API menjalankan kasus yang sama ke keduanya.
- **Model:** model dari zip dosen (3 masukan, 5 aturan, konsekuen monoton), bukan model 4 kriteria berbobot dari repo SpotWise lama.
- **Perhitungan wajib Python:** ketentuan tugas. Frontend tidak menghitung skor; ia hanya mengirim input dan menampilkan hasil dari API.
- **Satu web:** beranda dan aplikasi dalam satu proyek React, dipisah lewat hash (`#/`, `#/app`) supaya jalan di GitHub Pages tanpa pengaturan server.
- **Hitung ulang otomatis:** tiap input berubah, web memanggil API lagi (jeda 350 ms, permintaan lama dibatalkan).
- **Tautan Google Maps:** dibentuk dari nama + alamat supaya langsung membuka kafenya. Kolom `link_maps` di Excel hanya berisi teks "Buka di Maps", dan tautan koordinat saja ditolak.
- **Istilah:** UI memakai "kafe", bukan "kedai" atau "tempat". Nama fungsi internal `tsukamoto_tempat` sengaja tidak diganti.
- **Commit:** tanpa Claude sebagai contributor (author `SpotWise <noreply@github.com>`, tanpa trailer Co-Authored-By), dan hanya bila diminta.
- **Data:** `*.xlsx` tidak ikut git, kecuali `backend/data/coffee-depok-sleman.xlsx`; foto di `backend/data/foto/` ikut git. Alasannya: server hasil deploy langsung berisi data contoh. Foto berasal dari Google Maps, jadi periksa hak ciptanya sebelum repo dibuka untuk umum.

## Catatan teknis

- Backend dan web berjalan sendiri-sendiri: nyalakan `uvicorn api:app --port 8000` (dari `backend/`) dan `npm run dev` (dari `frontend/`).
- Streamlit menyimpan modul yang sudah diimpor: restart server setelah mengubah `tabel.py`, `carousel.py`, atau `fuzzy_core.py`. `uvicorn --reload` memuat ulang otomatis.
- Pages harus bersumber GitHub Actions. Dengan "Deploy from a branch", yang tampil kode mentah dan halamannya kosong.
- Di paket gratis, backend biasanya "tidur" bila lama tidak dipakai, jadi permintaan pertama bisa lambat.
