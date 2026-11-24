# Metode: Fuzzy Tsukamoto

Implementasi: `backend/fuzzy_core.py`. Tes: `backend/tests/test_fuzzy_core.py`.

## 1. Jarak

Jarak pengguna ke kafe dihitung dengan rumus Haversine (km), dari koordinat pengguna dan kolom `lat`, `lng`.

## 2. Fuzzifikasi

Semua fungsi keanggotaan linier. `clamp(x)` membatasi nilai ke 0–1.

| Variabel | Himpunan | Rumus |
|---|---|---|
| Jarak (km) | Dekat | `clamp((10 − jarak) / 8)` |
|  | Jauh | `clamp((jarak − 2) / 8)` |
| Rating | Tinggi | `clamp((rating − 4,2) / 0,8)` |
|  | Rendah | `clamp((5,0 − rating) / 0,8)` |
| Harga (Rp) | Murah | 1 sampai 20.000, turun linier ke 0 di 35.000 |
|  | Mahal | 0 sampai 50.000, naik linier ke 1 di 70.000 |
|  | Sedang | `1 − murah − mahal` |

### Keanggotaan harga

Maps memberi **rentang** harga per orang (mis. "Rp 25–50 rb" = 25.000 sampai 50.000), bukan satu angka.
Derajat murah, sedang, dan mahal adalah **rata-rata keanggotaan di sepanjang rentang** itu (`keanggotaan_harga()`).

- `harga_min = 1` berarti batas bawah kategori termurah Maps ("Rp 1–25.000"), dihitung sebagai 0.
- Harga kosong dianggap Rp 25–50 rb.
- Bila Excel sudah punya kolom `mu_murah`, `mu_sedang`, `mu_mahal`, nilai itu yang dipakai.
- Fungsi ini dicocokkan dengan 171 baris Excel lama dan selisihnya di bawah 0,003.

## 3. Inferensi (5 aturan, AND = min)

| Aturan | Kondisi | Konsekuen |
|---|---|---|
| R1 | dekat AND rating tinggi AND harga murah | skor tinggi |
| R2 | dekat AND rating tinggi AND harga sedang | skor tinggi |
| R3 | dekat AND rating tinggi AND harga mahal | rendah (mode **Hemat**) / tinggi (mode **Bebas**) |
| R4 | dekat AND rating rendah | skor rendah |
| R5 | jauh | skor rendah |

Kekuatan aturan α adalah nilai minimum dari semua premisnya (R5 hanya satu premis, jadi α = `jauh`).

## 4. Konsekuen monoton Tsukamoto

Skor 0–100. Setiap aturan menghasilkan nilai tegas z dari α-nya:

- konsekuen **tinggi**: `z = 100 · α`
- konsekuen **rendah**: `z = 100 · (1 − α)`

## 5. Defuzzifikasi

Rata-rata terbobot: `z* = Σ(α · z) / Σα`. Bila Σα = 0, skor 0.
Kafe diurutkan dari z* tertinggi.

## Filter (tegas, sebelum diurutkan)

Jarak maksimum, kecamatan, jenis kafe (`Kedai Kopi`, `Kafe`, `Lainnya`), dan hanya yang buka 24 jam.

## Catatan batas

- Batas himpunan (4,2 untuk rating, 10 km untuk jarak, dan seterusnya) adalah pilihan model, bukan hasil pembelajaran dari data. Ubah di `fuzzy_core.py` bila perlu, lalu perbarui tabel di atas.
- Skor hanya membandingkan kafe dalam satu kumpulan data. Skor 80 di satu kota tidak sebanding dengan skor 80 di kota lain.
