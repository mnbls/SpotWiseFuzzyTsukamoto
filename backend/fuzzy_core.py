"""Inti perhitungan fuzzy Tsukamoto untuk rekomendasi kafe (Jangkar Coffee)."""
import math


def clamp(x):
    return max(0.0, min(1.0, x))


def haversine(lat1, lng1, lat2, lng2):
    """Jarak dua titik di bumi dalam km."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def keanggotaan_harga(hmin, hmax):
    """Derajat keanggotaan harga (murah, sedang, mahal) untuk rentang harga Maps [hmin, hmax].

    Murah: 1 sampai Rp 20.000, turun linier ke 0 di Rp 35.000.
    Mahal: 0 sampai Rp 50.000, naik linier ke 1 di Rp 70.000.
    Sedang = 1 - murah - mahal. Nilai akhir = rata-rata keanggotaan di sepanjang rentang harga.
    Harga kosong dianggap Rp 25-50 rb. Rp 1 (batas bawah kategori termurah) dianggap 0.
    """
    if hmin is None or hmax is None or hmin != hmin or hmax != hmax:
        hmin, hmax = 25000, 50000
    hmin = 0 if hmin <= 1 else hmin
    n = 2001
    xs = [hmin + (hmax - hmin) * i / (n - 1) for i in range(n)]
    murah = sum(clamp((35000 - x) / 15000) for x in xs) / n
    mahal = sum(clamp((x - 50000) / 20000) for x in xs) / n
    return murah, max(0.0, 1 - murah - mahal), mahal


def label_harga(hmin, hmax):
    if hmin is None or hmax is None or hmin != hmin or hmax != hmax:
        return "Rp 25–50 rb (estimasi)"
    hmin = 0 if hmin <= 1 else hmin
    if hmin == hmax:
        return f"Rp {hmax / 1000:g} rb+"
    return f"Rp {hmin / 1000:g}–{hmax / 1000:g} rb" if hmin else f"Rp 1–{hmax / 1000:g} rb"


RULES = [
    "R1: IF dekat AND rating tinggi AND harga murah THEN skor tinggi",
    "R2: IF dekat AND rating tinggi AND harga sedang THEN skor tinggi",
    "R3: IF dekat AND rating tinggi AND harga mahal THEN skor rendah (mode Hemat) / tinggi (mode Bebas)",
    "R4: IF dekat AND rating rendah THEN skor rendah",
    "R5: IF jauh THEN skor rendah",
]


def fuzzifikasi(jarak_km, rating):
    """Derajat keanggotaan jarak (dekat/jauh) dan rating (tinggi/rendah)."""
    return {
        "dekat": clamp((10 - jarak_km) / 8),
        "jauh": clamp((jarak_km - 2) / 8),
        "rating_tinggi": clamp((rating - 4.2) / 0.8),
        "rating_rendah": clamp((5.0 - rating) / 0.8),
    }


def tsukamoto_tempat(jarak_km, rating, mu_murah, mu_sedang, mu_mahal, hemat=True):
    # 1) Fuzzifikasi
    f = fuzzifikasi(jarak_km, rating)
    dekat, jauh, r_tinggi, r_rendah = f["dekat"], f["jauh"], f["rating_tinggi"], f["rating_rendah"]
    # 2) Inferensi (AND = MIN). Konsekuen: Tinggi -> z = 100*a ; Rendah -> z = 100*(1-a)
    hasil_mahal = "rendah" if hemat else "tinggi"
    rules = [
        (min(dekat, r_tinggi, mu_murah), "tinggi"),     # R1
        (min(dekat, r_tinggi, mu_sedang), "tinggi"),    # R2
        (min(dekat, r_tinggi, mu_mahal), hasil_mahal),  # R3
        (min(dekat, r_rendah), "rendah"),               # R4
        (jauh, "rendah"),                               # R5
    ]
    zs = [(a, 100 * a if k == "tinggi" else 100 * (1 - a)) for a, k in rules]
    # 3) Defuzzifikasi: rata-rata terbobot
    den = sum(a for a, _ in zs)
    z = sum(a * zi for a, zi in zs) / den if den else 0.0
    return z, zs
