import base64
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from carousel import carousel_kafe, foto_uri
from fuzzy_core import RULES, tsukamoto_tempat
from rekomendasi import DataTidakValid, hitung, link_rute, muat_data as _muat_data, saring
from tabel import tabel_hasil

BASE = Path(__file__).parent  # semua path relatif terhadap folder backend/, dari mana pun dijalankan

st.set_page_config(page_title="Jangkar Coffee – Rekomendasi Kafe", page_icon=str(BASE / "logo.svg"), layout="wide")

# ---------- Tema: sama dengan beranda (krem hangat, tinta hitam, aksen oranye) ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp button, .stApp input, .stApp h1, .stApp h2, .stApp h3,
.stApp span:not([data-testid="stIconMaterial"]) { font-family: 'Onest', sans-serif; }
.stApp { background: #f8f7f3; }
#MainMenu, footer, [data-testid="stDeployButton"] { display: none; }
[data-testid="stSidebar"] { background: #efede6; border-right: 1px solid #d9d6d0; }
.block-container { max-width: 1280px; padding-top: 2rem; }
.sw-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 1.25rem; }
.sw-brand img { width: 40px; height: 40px; }
.sw-brand span { font-size: 1.8rem; font-weight: 500; letter-spacing: -0.04em; color: #171717; }
.sw-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 .6rem; font-size: .75rem;
  font-weight: 500; letter-spacing: .22em; text-transform: uppercase; color: #74716c; }
.sw-eyebrow::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #ff7a2f; }
h1 { font-weight: 400 !important; letter-spacing: -0.03em !important; line-height: 1.1 !important; color: #171717; }
h1 em { font-style: normal; color: #ff7a2f; }
h2, h3 { font-weight: 500 !important; letter-spacing: -0.02em !important; }
[data-testid="stDataFrame"], [data-testid="stExpander"], [data-testid="stFileUploader"] section {
  border-radius: 20px; border: 1px solid #d9d6d0; background: #fff; overflow: hidden; }
[data-testid="stFileUploader"] section { background: #f8f7f3; }
.stButton > button, [data-testid="stFileUploader"] button { border-radius: 999px; border: 1px solid #d9d6d0; }
</style>
""",
    unsafe_allow_html=True,
)

_logo = (BASE / "logo.svg").read_text(encoding="utf-8")
_logo_uri = "data:image/svg+xml;base64," + base64.b64encode(_logo.encode()).decode()
st.markdown(
    f'<div class="sw-brand"><img src="{_logo_uri}" alt=""><span>Jangkar Coffee</span></div>'
    '<p class="sw-eyebrow">Sistem Pendukung Keputusan</p>',
    unsafe_allow_html=True,
)
st.markdown(
    "# Temukan kafe terbaik dengan Fuzzy <em>Tsukamoto.</em>", unsafe_allow_html=True
)

FOLDER_FOTO = [BASE / "data" / "foto"]
BERKAS_BAWAAN = [BASE / "data" / "coffee-depok-sleman.xlsx", BASE / "data" / "coffee-sleman-harga.xlsx"]
muat_data = st.cache_data(_muat_data)  # logika data ada di rekomendasi.py, dipakai juga oleh API


# ---------- Sumber data: upload, atau berkas bawaan di folder ----------
st.sidebar.header("Data")
berkas = st.sidebar.file_uploader("Upload data kafe (.xlsx)", type="xlsx")
fotos = st.sidebar.file_uploader(
    "Upload foto kafe (opsional)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
    help="Nama file harus sama dengan isi kolom foto di Excel. Tanpa ini, foto dicari di backend/data/foto/.",
)
unggahan = {f.name: (f.getvalue(), f.type) for f in fotos}
bawaan = next((b for b in BERKAS_BAWAAN if b.is_file()), BERKAS_BAWAAN[0])
try:
    df = muat_data(berkas if berkas else bawaan)
except FileNotFoundError:
    st.info("Upload file Excel data kafe di sidebar untuk memulai.")
    st.stop()
except DataTidakValid as e:
    st.error(str(e))
    st.stop()

# ---------- Sidebar: input & filter ----------
st.session_state.setdefault("lat", -7.7600)
st.session_state.setdefault("lng", 110.4090)
if "titik_baru" in st.session_state:  # titik dari klik peta, diterapkan sebelum kolom input dibuat
    st.session_state["lat"], st.session_state["lng"] = st.session_state.pop("titik_baru")

st.sidebar.header("Lokasi kamu")
lat = st.sidebar.number_input("Latitude", key="lat", format="%.6f", step=0.001)
lng = st.sidebar.number_input("Longitude", key="lng", format="%.6f", step=0.001)
pilih_peta = st.sidebar.toggle("Pilih titik di peta", help="Klik peta untuk memindahkan lokasimu.")

st.sidebar.header("Preferensi (input fuzzy)")
hemat = st.sidebar.radio("Soal harga", ["Hemat", "Bebas"]) == "Hemat"

st.sidebar.header("Filter (crisp)")
kec = st.sidebar.multiselect("Kecamatan", sorted(df["kecamatan"].unique()))
jenis = st.sidebar.multiselect("Jenis kafe", ["Kedai Kopi", "Kafe", "Lainnya"])
maks_km = st.sidebar.slider("Jarak maksimum (km)", 1, 20, 10)
hanya_24 = st.sidebar.checkbox("Hanya yang buka 24 jam")

# ---------- Pilih titik di peta ----------
if pilih_peta:
    st.subheader("Pilih lokasimu di peta")
    st.caption("Klik di peta untuk menaruh titikmu. Titik abu-abu adalah kafe dari data.")
    peta = folium.Map(location=[lat, lng], zoom_start=13, control_scale=True)
    for r in df.itertuples():
        folium.CircleMarker(
            [r.lat, r.lng], radius=4, color="#74716c", weight=1, fill=True,
            fill_color="#74716c", fill_opacity=0.6, tooltip=str(r.nama_maps),
        ).add_to(peta)
    folium.Marker([lat, lng], tooltip="Lokasimu", icon=folium.Icon(color="orange", icon="user", prefix="fa")).add_to(peta)
    klik = st_folium(peta, height=380, use_container_width=True, returned_objects=["last_clicked"], key="peta_pilih")
    if klik and klik.get("last_clicked"):
        titik = (round(klik["last_clicked"]["lat"], 6), round(klik["last_clicked"]["lng"], 6))
        if titik != st.session_state.get("_klik_terakhir"):
            st.session_state["_klik_terakhir"] = titik
            st.session_state["titik_baru"] = titik
            st.rerun()

# ---------- Proses ----------
df = hitung(df, lat, lng, hemat)
hasil = saring(df, maks_km, kec, jenis, hanya_24)

# ---------- Tampilan ----------
st.subheader(f"{len(hasil)} kafe ditemukan")
hasil = hasil.assign(link_rute=[link_rute(lat, lng, q) for q in hasil["kueri_maps"]])

# Rekomendasi teratas: kartu foto yang bisa digeser, langsung buka kafenya atau rute ke sana
if len(hasil):
    teratas = hasil.head(10)
    carousel_kafe([
        {
            "nama": r.nama_maps,
            "foto": foto_uri(getattr(r, "foto", None), FOLDER_FOTO, unggahan),
            "rating": float(r.rating),
            "jenis": r.jenis,
            "harga": getattr(r, "harga_label", ""),
            "jarak": float(r.jarak_km),
            "skor": float(r.skor),
            "maps": r.link_maps,
            "rute": r.link_rute,
        }
        for r in teratas.itertuples()
    ])

tabel_hasil(hasil.head(20))
st.map(hasil.head(20).rename(columns={"lng": "lon"}), latitude="lat", longitude="lon", color="#ff7a2f")

# ---------- Rincian perhitungan ----------
if len(hasil):
    with st.expander("Perhitungan fuzzy kafe teratas"):
        t = hasil.iloc[0]
        z, zs = tsukamoto_tempat(
            t.jarak_km, t.rating, t.mu_murah, t.mu_sedang, t.mu_mahal, hemat)
        st.write(f"**{t.nama_maps}** — jarak {t.jarak_km:.2f} km, rating {t.rating}")
        st.dataframe(
            pd.DataFrame({
                "Aturan": RULES,
                "α (min)": [a for a, _ in zs],
                "z": [zi for _, zi in zs],
                "α × z": [a * zi for a, zi in zs],
            }),
            hide_index=True,
            width="stretch",
        )
        st.write(f"z akhir = Σ(α·z) / Σα = **{z:.2f}**")
