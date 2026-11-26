"""API Jangkar Coffee versi WSGI murni (Flask), untuk PythonAnywhere.

Server web PythonAnywhere tidak menjalankan thread Python, sehingga FastAPI (lewat adapter ASGI→WSGI) macet di sana.
Versi ini memakai logika yang sama (layanan.py) dan membalas dengan bentuk JSON yang sama seperti api.py.

Berkas WSGI di PythonAnywhere (/var/www/<username>_pythonanywhere_com_wsgi.py):

    import sys
    sys.path.insert(0, "/home/<username>/jangkar/backend")
    from wsgi_flask import app as application  # noqa: E402,F401
"""
from flask import Flask, jsonify, request, send_from_directory

import layanan
from layanan import ASAL_CORS, FOLDER_FOTO, MAKS_EXCEL, MAKS_FOTO, MAKS_JUMLAH_FOTO, GalatLayanan

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAKS_EXCEL + MAKS_JUMLAH_FOTO * MAKS_FOTO + 1024 * 1024
app.json.ensure_ascii = False


@app.after_request
def _cors(resp):
    asal = request.headers.get("Origin")
    if "*" in ASAL_CORS:
        resp.headers["Access-Control-Allow-Origin"] = "*"
    elif asal in ASAL_CORS:
        resp.headers["Access-Control-Allow-Origin"] = asal
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = request.headers.get("Access-Control-Request-Headers", "*")
    return resp


@app.errorhandler(GalatLayanan)
def _galat(e: GalatLayanan):
    return jsonify(detail=e.pesan), e.status


@app.errorhandler(413)
def _terlalu_besar(_):
    return jsonify(detail="Unggahan terlalu besar."), 413


def _angka(nama, bawaan, jenis=float):
    nilai = request.form.get(nama)
    if nilai is None or nilai == "":
        if bawaan is None:
            raise GalatLayanan(422, f"Input tidak valid: {nama} wajib diisi.")
        return bawaan
    try:
        return jenis(nilai)
    except ValueError:
        raise GalatLayanan(422, f"Input tidak valid: {nama} harus angka.") from None


def _bool(nama, bawaan):
    nilai = request.form.get(nama)
    return bawaan if nilai is None else nilai.strip().lower() in ("true", "1", "ya", "on")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/meta")
def meta():
    return jsonify(layanan.ringkasan_meta())


@app.route("/api/rekomendasi", methods=["POST", "OPTIONS"])
def rekomendasi():
    if request.method == "OPTIONS":
        return "", 204
    berkas = request.files.get("berkas")
    excel = (berkas.filename, berkas.stream.read(MAKS_EXCEL + 1)) if berkas and berkas.filename else None
    gambar = [(f.filename, f.mimetype, f.stream.read(MAKS_FOTO + 1)) for f in request.files.getlist("foto")]
    return jsonify(layanan.hitung_rekomendasi(
        lat=_angka("lat", None),
        lng=_angka("lng", None),
        hemat=_bool("hemat", True),
        maks_km=_angka("maks_km", 10.0),
        kecamatan=request.form.getlist("kecamatan"),
        jenis=request.form.getlist("jenis"),
        hanya_24=_bool("hanya_24", False),
        limit=_angka("limit", 10, int),
        berkas=excel,
        foto=gambar,
    ))


@app.get("/foto/<path:nama>")
def foto(nama):
    return send_from_directory(FOLDER_FOTO, nama)  # menolak path di luar folder foto
