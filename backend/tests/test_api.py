"""Tes API. Jalankan dari folder backend/:  python -m unittest discover tests  (butuh httpx, lihat requirements-dev.txt)"""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402

klien = TestClient(api.app)
LOKASI = {"lat": "-7.76", "lng": "110.409"}


def _xlsx(baris, kolom=None):
    buf = io.BytesIO()
    pd.DataFrame(baris, columns=kolom).to_excel(buf, sheet_name="Data", index=False)
    return buf.getvalue()


def _unggah(isi, nama="data.xlsx"):
    return {"berkas": (nama, isi, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


CONTOH = [
    {"nama_maps": "Dekat Murah", "rating": 4.9, "lat": -7.761, "lng": 110.410, "harga_min": 0, "harga_max": 25000},
    {"nama_maps": "Jauh Mahal", "rating": 4.9, "lat": -7.900, "lng": 110.600, "harga_min": 75000, "harga_max": 225000},
    {"nama_maps": "Dekat Rating Rendah", "rating": 3.5, "lat": -7.762, "lng": 110.411, "harga_min": 25000, "harga_max": 50000},
]


class Api(unittest.TestCase):
    def test_health(self):
        self.assertEqual(klien.get("/api/health").json(), {"status": "ok"})

    def test_urutan_dan_bentuk_hasil(self):
        r = klien.post("/api/rekomendasi", data={**LOKASI, "maks_km": "50"}, files=_unggah(_xlsx(CONTOH)))
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["jumlah"], 3)
        nama = [h["nama"] for h in j["hasil"]]
        self.assertEqual(nama[0], "Dekat Murah")
        skor = [h["skor"] for h in j["hasil"]]
        self.assertEqual(skor, sorted(skor, reverse=True))
        h = j["hasil"][0]
        self.assertEqual(h["peringkat"], 1)
        self.assertEqual(len(h["perhitungan"]["aturan"]), 5)
        self.assertAlmostEqual(h["perhitungan"]["z_akhir"], h["skor"])
        self.assertTrue(h["maps"].startswith("https://www.google.com/maps/search/"))
        self.assertIn("destination=", h["rute"])

    def test_filter_jarak(self):
        r = klien.post("/api/rekomendasi", data={**LOKASI, "maks_km": "5"}, files=_unggah(_xlsx(CONTOH)))
        self.assertNotIn("Jauh Mahal", [h["nama"] for h in r.json()["hasil"]])

    def test_mode_hemat_dan_bebas_beda_untuk_harga_mahal(self):
        mahal = [{"nama_maps": "Mahal", "rating": 5.0, "lat": -7.7601, "lng": 110.409, "harga_min": 250000, "harga_max": 250000}]
        hemat = klien.post("/api/rekomendasi", data={**LOKASI, "hemat": "true"}, files=_unggah(_xlsx(mahal))).json()
        bebas = klien.post("/api/rekomendasi", data={**LOKASI, "hemat": "false"}, files=_unggah(_xlsx(mahal))).json()
        self.assertLess(hemat["hasil"][0]["skor"], bebas["hasil"][0]["skor"])

    def test_kolom_kurang_ditolak(self):
        r = klien.post("/api/rekomendasi", data=LOKASI, files=_unggah(_xlsx([{"nama_maps": "X", "rating": 4}])))
        self.assertEqual(r.status_code, 400)
        self.assertIn("Kolom wajib", r.json()["detail"])

    def test_bukan_excel_ditolak(self):
        r = klien.post("/api/rekomendasi", data=LOKASI, files=_unggah(b"bukan excel"))
        self.assertEqual(r.status_code, 400)

    def test_koordinat_tidak_valid(self):
        r = klien.post("/api/rekomendasi", data={"lat": "999", "lng": "0"}, files=_unggah(_xlsx(CONTOH)))
        self.assertEqual(r.status_code, 422)

    def test_foto_unggahan_jadi_data_uri(self):
        data = [{**CONTOH[0], "foto": "a.jpg"}]
        files = {**_unggah(_xlsx(data)), "foto": ("a.jpg", b"\xff\xd8\xff", "image/jpeg")}
        h = klien.post("/api/rekomendasi", data=LOKASI, files=files).json()["hasil"][0]
        self.assertTrue(h["foto"].startswith("data:image/jpeg;base64,"))

    def test_foto_tidak_ada_jadi_null(self):
        data = [{**CONTOH[0], "foto": "tidak-ada.jpg"}]
        h = klien.post("/api/rekomendasi", data=LOKASI, files=_unggah(_xlsx(data))).json()["hasil"][0]
        self.assertIsNone(h["foto"])


if __name__ == "__main__":
    unittest.main()
