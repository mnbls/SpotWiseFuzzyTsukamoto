import pandas as pd
import streamlit as st
from fuzzy_core import RULES, haversine, tsukamoto_tempat

st.set_page_config(page_title="SpotWise – Rekomendasi Tempat", page_icon="📍", layout="wide")
st.title("SpotWise – Rekomendasi Tempat Terbaik (Fuzzy Tsukamoto)")

WAJIB = ["nama_maps", "rating", "lat", "lng", "mu_murah", "mu_sedang", "mu_mahal"]


@st.cache_data
def muat_data(sumber):
    df = pd.read_excel(sumber, sheet_name="Data")
    df["kecamatan"] = df["kecamatan"].fillna("Tidak diketahui")
    utama = df["kategori"].isin(["Kedai Kopi", "Kafe"])
    df["jenis"] = df["kategori"].where(utama, "Lainnya")
    return df


# ---------- Sumber data: upload, atau berkas bawaan di folder ----------
st.sidebar.header("Data")
berkas = st.sidebar.file_uploader("Upload data tempat (.xlsx)", type="xlsx")
try:
    df = muat_data(berkas if berkas else "coffee-sleman-harga.xlsx")
except FileNotFoundError:
    st.info("Upload file Excel data tempat di sidebar untuk memulai.")
    st.stop()
kurang = [k for k in WAJIB if k not in df.columns]
if kurang:
    st.error("Kolom wajib tidak ada di file: " + ", ".join(kurang))
    st.stop()

# ---------- Sidebar: input & filter ----------
st.sidebar.header("Lokasi kamu")
lat = st.sidebar.number_input("Latitude", value=-7.7600, format="%.6f")
lng = st.sidebar.number_input("Longitude", value=110.4090, format="%.6f")

st.sidebar.header("Preferensi (input fuzzy)")
hemat = st.sidebar.radio("Soal harga", ["Hemat", "Bebas"]) == "Hemat"

st.sidebar.header("Filter (crisp)")
kec = st.sidebar.multiselect("Kecamatan", sorted(df["kecamatan"].unique()))
jenis = st.sidebar.multiselect("Jenis tempat", ["Kedai Kopi", "Kafe", "Lainnya"])
maks_km = st.sidebar.slider("Jarak maksimum (km)", 1, 20, 10)
hanya_24 = st.sidebar.checkbox("Hanya yang buka 24 jam")

# ---------- Proses ----------
df["jarak_km"] = [haversine(lat, lng, a, b) for a, b in zip(df["lat"], df["lng"])]
df["skor"] = [
    tsukamoto_tempat(r.jarak_km, r.rating, r.mu_murah, r.mu_sedang, r.mu_mahal, hemat)[0]
    for r in df.itertuples()
]

hasil = df[df["jarak_km"] <= maks_km]
if kec:
    hasil = hasil[hasil["kecamatan"].isin(kec)]
if jenis:
    hasil = hasil[hasil["jenis"].isin(jenis)]
if hanya_24:
    hasil = hasil[hasil["buka_24_jam"] == "Ya"]
hasil = hasil.sort_values("skor", ascending=False)

# ---------- Tampilan ----------
st.subheader(f"{len(hasil)} tempat ditemukan")
kolom = ["nama_maps", "kecamatan", "harga_label", "rating", "jarak_km", "skor", "link_maps"]
st.dataframe(
    hasil[kolom].head(20),
    column_config={
        "skor": st.column_config.ProgressColumn(
            "Skor", min_value=0, max_value=100, format="%.1f"),
        "jarak_km": st.column_config.NumberColumn("Jarak (km)", format="%.2f"),
        "link_maps": st.column_config.LinkColumn("Peta", display_text="Buka"),
    },
    hide_index=True,
    width="stretch",
)
st.map(hasil.head(20).rename(columns={"lng": "lon"}), latitude="lat", longitude="lon")

# ---------- Rincian perhitungan ----------
if len(hasil):
    with st.expander("Perhitungan fuzzy tempat teratas"):
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
