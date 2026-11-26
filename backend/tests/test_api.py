"""Tes API: kasus yang sama dijalankan terhadap FastAPI (api.py) dan Flask (wsgi_flask.py).

Jalankan dari folder backend/:  python -m unittest discover tests  (butuh httpx dan flask, lihat requirements-dev.txt)
"""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402
import wsgi_flask  # noqa: E402

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
LOKASI = {"lat": "-7.76", "lng": "110.409"}
CONTOH = [
    {"nama_maps": "Dekat Murah", "rating": 4.9, "lat": -7.761, "lng": 110.410, "harga_min": 0, "harga_max": 25000},
    {"nama_maps": "Jauh Mahal", "rating": 4.9, "lat": -7.900, "lng": 110.600, "harga_min": 75000, "harga_max": 225000},
    {"nama_maps": "Dekat Rating Rendah", "rating": 3.5, "lat": -7.762, "lng": 110.411, "harga_min": 25000, "harga_max": 50000},
]


def _xlsx(baris):
    buf = io.BytesIO()
    pd.DataFrame(baris).to_excel(buf, sheet_name="Data", index=False)
    return buf.getvalue()


class _Klien:
    """Bungkus klien tes supaya kasus yang sama jalan di kedua kerangka. Balas (status, json, header)."""

    def get(self, url):
        raise NotImplementedError

    def post(self, data, excel=None, foto=()):
        raise NotImplementedError


class _KlienFastAPI(_Klien):
    c = TestClient(api.app)

    def get(self, url):
        r = self.c.get(url)
        return r.status_code, r.json() if "json" in r.headers.get("content-type", "") else None, r.headers

    def post(self, data, excel=None, foto=()):
        files = []
        if excel is not None:
            files.append(("berkas", ("data.xlsx", excel, XLSX)))
        files += [("foto", f) for f in foto]
        r = self.c.post("/api/rekomendasi", data=data, files=files or None)
        return r.status_code, r.json(), r.headers


class _KlienFlask(_Klien):
    c = wsgi_flask.app.test_client()

    def get(self, url):
        r = self.c.get(url, headers={"Origin": "https://mnbls.github.io"})
        return r.status_code, r.get_json(silent=True), r.headers

    def post(self, data, excel=None, foto=()):
        isi = dict(data)
        if excel is not None:
            isi["berkas"] = (io.BytesIO(excel), "data.xlsx", XLSX)
        if foto:
            isi["foto"] = [(io.BytesIO(b), n, t) for n, b, t in foto]
        r = self.c.post("/api/rekomendasi", data=isi, content_type="multipart/form-data")
        return r.status_code, r.get_json(), r.headers


class _KasusApi:
    klien: _Klien

    def test_health(self):
        status, j, _ = self.klien.get("/api/health")
        self.assertEqual((status, j), (200, {"status": "ok"}))

    def test_meta_data_bawaan(self):
        status, j, _ = self.klien.get("/api/meta")
        self.assertEqual(status, 200)
        self.assertIn("tersedia", j)

    def test_urutan_dan_bentuk_hasil(self):
        status, j, _ = self.klien.post({**LOKASI, "maks_km": "50"}, _xlsx(CONTOH))
        self.assertEqual(status, 200, j)
        self.assertEqual(j["jumlah"], 3)
        self.assertEqual(j["hasil"][0]["nama"], "Dekat Murah")
        skor = [h["skor"] for h in j["hasil"]]
        self.assertEqual(skor, sorted(skor, reverse=True))
        h = j["hasil"][0]
        self.assertEqual(h["peringkat"], 1)
        self.assertEqual(len(h["perhitungan"]["aturan"]), 5)
        self.assertAlmostEqual(h["perhitungan"]["z_akhir"], h["skor"])
        self.assertTrue(h["maps"].startswith("https://www.google.com/maps/search/"))
        self.assertIn("destination=", h["rute"])
        self.assertEqual(j["kecamatan_tersedia"], ["Tidak diketahui"])

    def test_filter_jarak(self):
        _, j, _ = self.klien.post({**LOKASI, "maks_km": "5"}, _xlsx(CONTOH))
        self.assertNotIn("Jauh Mahal", [h["nama"] for h in j["hasil"]])

    def test_mode_hemat_dan_bebas_beda_untuk_harga_mahal(self):
        mahal = _xlsx([{"nama_maps": "Mahal", "rating": 5.0, "lat": -7.7601, "lng": 110.409, "harga_min": 250000, "harga_max": 250000}])
        _, hemat, _ = self.klien.post({**LOKASI, "hemat": "true"}, mahal)
        _, bebas, _ = self.klien.post({**LOKASI, "hemat": "false"}, mahal)
        self.assertLess(hemat["hasil"][0]["skor"], bebas["hasil"][0]["skor"])

    def test_kolom_kurang_ditolak(self):
        status, j, _ = self.klien.post(LOKASI, _xlsx([{"nama_maps": "X", "rating": 4}]))
        self.assertEqual(status, 400)
        self.assertIn("Kolom wajib", j["detail"])

    def test_bukan_excel_ditolak(self):
        status, _, _ = self.klien.post(LOKASI, b"bukan excel")
        self.assertEqual(status, 400)

    def test_koordinat_tidak_valid(self):
        status, j, _ = self.klien.post({"lat": "999", "lng": "0"}, _xlsx(CONTOH))
        self.assertEqual(status, 422)

    def test_foto_unggahan_jadi_data_uri(self):
        data = _xlsx([{**CONTOH[0], "foto": "a.jpg"}])
        _, j, _ = self.klien.post(LOKASI, data, foto=[("a.jpg", b"\xff\xd8\xff", "image/jpeg")])
        self.assertTrue(j["hasil"][0]["foto"].startswith("data:image/jpeg;base64,"))

    def test_foto_tidak_ada_jadi_null(self):
        _, j, _ = self.klien.post(LOKASI, _xlsx([{**CONTOH[0], "foto": "tidak-ada.jpg"}]))
        self.assertIsNone(j["hasil"][0]["foto"])


class ApiFastAPI(_KasusApi, unittest.TestCase):
    klien = _KlienFastAPI()


class ApiFlask(_KasusApi, unittest.TestCase):
    klien = _KlienFlask()

    def test_cors_dan_preflight(self):
        r = _KlienFlask.c.options("/api/rekomendasi", headers={"Origin": "https://mnbls.github.io", "Access-Control-Request-Method": "POST"})
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "*")

    def test_foto_tidak_bisa_keluar_folder(self):
        r = _KlienFlask.c.get("/foto/../api.py")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
