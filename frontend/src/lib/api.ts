// Klien API Jangkar Coffee. Semua perhitungan fuzzy dijalankan di backend Python; di sini hanya mengirim dan menampilkan.

export const API_URL = String(import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export interface Aturan {
  aturan: string
  alpha: number
  z: number
  alpha_z: number
}

export interface Perhitungan {
  fuzzifikasi: {
    dekat: number
    jauh: number
    rating_tinggi: number
    rating_rendah: number
    murah: number
    sedang: number
    mahal: number
  }
  aturan: Aturan[]
  z_akhir: number
}

export interface Kafe {
  peringkat: number
  nama: string
  jenis: string
  kecamatan: string
  alamat: string
  harga: string
  rating: number
  jumlah_ulasan: number | null
  buka_24_jam: boolean
  jarak_km: number
  skor: number
  lat: number
  lng: number
  foto: string | null
  maps: string
  rute: string
  perhitungan: Perhitungan
}

export interface TitikPeta {
  nama: string
  lat: number
  lng: number
}

export interface Hasil {
  sumber: string
  mode: 'Hemat' | 'Bebas'
  total_data: number
  jumlah: number
  kecamatan_tersedia: string[]
  hasil: Kafe[]
  peta: TitikPeta[]
}

export interface Meta {
  tersedia: boolean
  sumber: string | null
  jumlah: number
  kecamatan: string[]
  jenis: string[]
  pusat: { lat: number; lng: number } | null
}

export interface Param {
  lat: number
  lng: number
  hemat: boolean
  maks_km: number
  kecamatan: string[]
  jenis: string[]
  hanya_24: boolean
  limit: number
}

async function periksa(r: Response) {
  if (r.ok) return r
  let pesan = `Server membalas ${r.status}.`
  try {
    const j = await r.json()
    if (typeof j.detail === 'string') pesan = j.detail
    else if (Array.isArray(j.detail) && j.detail[0]?.msg) pesan = `Input tidak valid: ${j.detail[0].msg}`
  } catch {
    /* badan bukan JSON */
  }
  throw new Error(pesan)
}

export async function ambilMeta(signal?: AbortSignal): Promise<Meta> {
  const r = await periksa(await fetch(`${API_URL}/api/meta`, { signal }))
  return r.json()
}

export async function cariRekomendasi(
  p: Param,
  berkas: File | null,
  foto: File[],
  signal?: AbortSignal
): Promise<Hasil> {
  const f = new FormData()
  f.set('lat', String(p.lat))
  f.set('lng', String(p.lng))
  f.set('hemat', String(p.hemat))
  f.set('maks_km', String(p.maks_km))
  f.set('hanya_24', String(p.hanya_24))
  f.set('limit', String(p.limit))
  p.kecamatan.forEach(k => f.append('kecamatan', k))
  p.jenis.forEach(j => f.append('jenis', j))
  if (berkas) f.set('berkas', berkas)
  foto.forEach(x => f.append('foto', x))
  const r = await periksa(await fetch(`${API_URL}/api/rekomendasi`, { method: 'POST', body: f, signal }))
  return r.json()
}

/** Foto bawaan dilayani backend (`/foto/...`); foto unggahan sudah berupa data-URI. */
export const urlFoto = (foto: string | null) => (!foto ? null : foto.startsWith('/') ? API_URL + foto : foto)

export const koma = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
