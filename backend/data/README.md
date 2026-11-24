# Data kafe

Data contoh untuk server: satu Excel hasil scraping dan foto-fotonya **ikut git**, supaya backend yang baru di-deploy langsung berisi data.

```
backend/data/
├── coffee-depok-sleman.xlsx     ← berkas bawaan (10 kafe di Depok, Sleman); ikut git
└── foto/                        ← gambar yang namanya ada di kolom `foto`; ikut git
```

Berkas `.xlsx` lain di folder ini tidak ikut git (lihat `.gitignore`); tambahkan pengecualian di sana bila perlu.
Pengguna juga bisa mengunggah Excel dan foto sendiri lewat web; unggahan menggantikan data bawaan untuk permintaan itu saja.
Foto berasal dari Google Maps. Sebelum repo dibuka untuk umum, pastikan penggunaannya sesuai ketentuan dan hak cipta foto tersebut.

Sheet `Data`, kolom wajib: `nama_maps, rating, lat, lng`.
Kolom yang dipakai bila ada: `foto, kategori, kecamatan, alamat, harga_min, harga_max, buka_24_jam`.
Kolom `mu_murah / mu_sedang / mu_mahal` opsional: bila tidak ada, dihitung dari `harga_min` dan `harga_max`.
