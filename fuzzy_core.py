"""Inti perhitungan fuzzy Tsukamoto untuk rekomendasi tempat (SpotWise)."""
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


RULES = [
    "R1: IF dekat AND rating tinggi AND harga murah THEN skor tinggi",
    "R2: IF dekat AND rating tinggi AND harga sedang THEN skor tinggi",
    "R3: IF dekat AND rating tinggi AND harga mahal THEN skor rendah (mode Hemat) / tinggi (mode Bebas)",
    "R4: IF dekat AND rating rendah THEN skor rendah",
    "R5: IF jauh THEN skor rendah",
]


def tsukamoto_tempat(jarak_km, rating, mu_murah, mu_sedang, mu_mahal, hemat=True):
    # 1) Fuzzifikasi
    dekat = clamp((10 - jarak_km) / 8)
    jauh = clamp((jarak_km - 2) / 8)
    r_tinggi = clamp((rating - 4.2) / 0.8)
    r_rendah = clamp((5.0 - rating) / 0.8)
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
