# SpotWise – Fuzzy Tsukamoto (beranda web + perhitungan Python)

**Repo:** https://github.com/mnbls/SpotWiseFuzzyTsukamoto.git

## Struktur
- **Beranda** (Vite + React + TS + Tailwind v4): `index.html`, `src/` (hero 3D `src/components/ui/syntra-hero.tsx`, tombol Mulai di `src/demo.tsx`). Dibuild ke GitHub Pages lewat `.github/workflows/deploy.yml` (Source Pages harus **GitHub Actions**)
- **Aplikasi + perhitungan** (Python, Streamlit): `app.py` (antarmuka: upload, lokasi, mode harga, filter, tabel, peta, rincian), `fuzzy_core.py` (Haversine + `tsukamoto_tempat()`), `requirements.txt`

## Alur
Beranda → tombol **Mulai** → aplikasi Streamlit (upload Excel → lokasi & preferensi → hasil).
Alamat aplikasi diatur di `src/demo.tsx` (`APP_URL`, atau env `VITE_APP_URL`). Isi dengan alamat hasil deploy di share.streamlit.io.

## Fuzzy Tsukamoto (fuzzy_core.py)
Masukan: jarak (dekat/jauh), rating (tinggi/rendah), harga (murah/sedang/mahal dari kolom `mu_*` di Excel).
5 aturan IF-THEN, AND = min. Konsekuen: tinggi → z = 100·α, rendah → z = 100·(1−α). Mode "Hemat": harga mahal → rendah; "Bebas": → tinggi.
Defuzzifikasi: z = Σ(α·z) / Σα.

## Menjalankan
- Python: `pip install -r requirements.txt` lalu `streamlit run app.py`
- Beranda: `npm install` lalu `npm run dev` (port 5174)

## Excel
Sheet `Data`, kolom wajib: `nama_maps, rating, lat, lng, mu_murah, mu_sedang, mu_mahal`; juga dipakai: `kategori, kecamatan, harga_label, buka_24_jam, link_maps`.
`*.xlsx` di-ignore git; `coffee-sleman-harga.xlsx` hanya cadangan lokal, di server pakai upload.

## Status
- [x] Beranda lama (tanpa gerbang upload) + aplikasi Python
- [ ] Commit & push ke repo baru
- [ ] Deploy Streamlit Community Cloud, isi `APP_URL`, set Pages = GitHub Actions
