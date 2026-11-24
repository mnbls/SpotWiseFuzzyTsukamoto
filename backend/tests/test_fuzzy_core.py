"""Tes inti fuzzy. Jalankan dari folder backend/:  python -m unittest discover tests"""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fuzzy_core import haversine, keanggotaan_harga, label_harga, tsukamoto_tempat  # noqa: E402


class Haversine(unittest.TestCase):
    def test_titik_sama_nol(self):
        self.assertAlmostEqual(haversine(-7.76, 110.41, -7.76, 110.41), 0.0)

    def test_satu_derajat_lintang_sekitar_111_km(self):
        self.assertAlmostEqual(haversine(0, 110, 1, 110), 111.19, delta=0.1)


class KeanggotaanHarga(unittest.TestCase):
    def assertMu(self, got, want):
        for g, w in zip(got, want):
            self.assertAlmostEqual(g, w, delta=0.003)

    def test_cocok_dengan_excel_lama(self):
        self.assertMu(keanggotaan_harga(25000, 50000), (0.1334, 0.8666, 0.0))
        self.assertMu(keanggotaan_harga(0, 25000), (0.9667, 0.0333, 0.0))
        self.assertMu(keanggotaan_harga(50000, 75000), (0.0, 0.4, 0.6))
        self.assertMu(keanggotaan_harga(25000, 125000), (0.0334, 0.3167, 0.65))
        self.assertMu(keanggotaan_harga(250000, 250000), (0.0, 0.0, 1.0))

    def test_rp1_dianggap_nol(self):
        self.assertMu(keanggotaan_harga(1, 25000), keanggotaan_harga(0, 25000))

    def test_harga_kosong_dianggap_25_sampai_50(self):
        self.assertMu(keanggotaan_harga(float("nan"), float("nan")), keanggotaan_harga(25000, 50000))

    def test_jumlah_selalu_satu(self):
        for a, b in [(0, 25000), (25000, 50000), (50000, 150000), (75000, 225000)]:
            self.assertAlmostEqual(sum(keanggotaan_harga(a, b)), 1.0)

    def test_label(self):
        self.assertEqual(label_harga(25000, 50000), "Rp 25–50 rb")
        self.assertEqual(label_harga(0, 25000), "Rp 1–25 rb")
        self.assertEqual(label_harga(250000, 250000), "Rp 250 rb+")


class Tsukamoto(unittest.TestCase):
    def test_dekat_rating_tinggi_murah_skor_tinggi(self):
        z, _ = tsukamoto_tempat(0.5, 5.0, 1, 0, 0)
        self.assertGreater(z, 90)

    def test_jauh_skor_nol(self):
        z, _ = tsukamoto_tempat(15, 5.0, 1, 0, 0)
        self.assertAlmostEqual(z, 0.0)

    def test_mode_hemat_menghukum_harga_mahal(self):
        hemat, _ = tsukamoto_tempat(0.5, 5.0, 0, 0, 1, hemat=True)
        bebas, _ = tsukamoto_tempat(0.5, 5.0, 0, 0, 1, hemat=False)
        self.assertLess(hemat, bebas)

    def test_skor_dalam_0_sampai_100_dan_ada_lima_aturan(self):
        z, zs = tsukamoto_tempat(3, 4.5, 0.2, 0.6, 0.2)
        self.assertTrue(0 <= z <= 100)
        self.assertEqual(len(zs), 5)
        self.assertFalse(math.isnan(z))


if __name__ == "__main__":
    unittest.main()
