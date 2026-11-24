import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, Loader2, ServerOff, Upload } from 'lucide-react'
import CarouselKafe from '@/components/app/CarouselKafe'
import FormPreferensi from '@/components/app/FormPreferensi'
import PetaKafe from '@/components/app/PetaKafe'
import RincianFuzzy from '@/components/app/RincianFuzzy'
import TabelHasil from '@/components/app/TabelHasil'
import { API_URL, ambilMeta, cariRekomendasi, type Hasil, type Meta, type Param } from '@/lib/api'

const AWAL: Param = { lat: -7.76, lng: 110.409, hemat: true, maks_km: 10, kecamatan: [], jenis: [], hanya_24: false, limit: 10 }

function Judul({ children }: { children: React.ReactNode }) {
  return <h2 className='mt-10 mb-3 text-xl font-medium tracking-tight'>{children}</h2>
}

export default function AplikasiPage() {
  const [p, setP] = useState<Param>(AWAL)
  const [berkas, setBerkas] = useState<File | null>(null)
  const [foto, setFoto] = useState<File[]>([])
  const [meta, setMeta] = useState<Meta | null>(null)
  const [siap, setSiap] = useState(false)
  const [hasil, setHasil] = useState<Hasil | null>(null)
  const [memuat, setMemuat] = useState(false)
  const [galat, setGalat] = useState<string | null>(null)
  const [pilih, setPilih] = useState(0)
  const [lokasiGalat, setLokasiGalat] = useState<string | null>(null)

  const ubah = useCallback((b: Partial<Param>) => setP(x => ({ ...x, ...b })), [])

  // Data bawaan: titik awal di tengah data. Bila backend mati, tampilkan petunjuk menyalakannya.
  useEffect(() => {
    const ac = new AbortController()
    ambilMeta(ac.signal)
      .then(m => {
        setMeta(m)
        if (m.pusat) setP(x => ({ ...x, lat: +m.pusat!.lat.toFixed(6), lng: +m.pusat!.lng.toFixed(6) }))
        setSiap(true)
      })
      .catch(e => {
        if (ac.signal.aborted) return
        setGalat(`Backend tidak terjangkau di ${API_URL}. ${e instanceof Error ? e.message : ''}`)
        setSiap(true)
      })
    return () => ac.abort()
  }, [])

  // Hitung ulang (di Python) tiap input berubah, dengan jeda singkat supaya tidak membanjiri server.
  // Server hidup tetapi belum punya data bawaan dan belum ada berkas yang diunggah: tunggu unggahan.
  const perluData = siap && !!meta && !meta.tersedia && !berkas

  useEffect(() => {
    if (!siap || perluData) return
    const ac = new AbortController()
    const id = setTimeout(() => {
      setMemuat(true)
      cariRekomendasi(p, berkas, foto, ac.signal)
        .then(h => {
          setHasil(h)
          setGalat(null)
          setPilih(0)
        })
        .catch(e => {
          if (ac.signal.aborted) return
          setGalat(e instanceof Error ? (e.message === 'Failed to fetch' ? `Backend tidak terjangkau di ${API_URL}.` : e.message) : 'Terjadi kesalahan.')
        })
        .finally(() => {
          if (!ac.signal.aborted) setMemuat(false)
        })
    }, 350)
    return () => {
      clearTimeout(id)
      ac.abort()
    }
  }, [siap, perluData, p, berkas, foto])

  const lokasiSaya = () => {
    setLokasiGalat(null)
    if (!navigator.geolocation) return setLokasiGalat('Browser ini tidak mendukung lokasi.')
    navigator.geolocation.getCurrentPosition(
      pos => ubah({ lat: +pos.coords.latitude.toFixed(6), lng: +pos.coords.longitude.toFixed(6) }),
      () => setLokasiGalat('Lokasi tidak diizinkan. Ketik koordinat atau klik peta.')
    )
  }

  const kafe = hasil?.hasil ?? []
  const terpilih = kafe[pilih] ?? kafe[0]
  const kecamatan = hasil?.kecamatan_tersedia ?? meta?.kecamatan ?? []

  return (
    <div className='bg-krem text-tinta min-h-screen font-sans'>
      <header className='border-garis border-b'>
        <div className='mx-auto flex max-w-[1360px] items-center justify-between px-5 py-4'>
          <a href='#/' className='text-tinta flex items-center gap-2.5 no-underline'>
            <img src='./favicon.svg' alt='' className='size-8' />
            <span className='text-[22px] font-medium tracking-[-0.04em]'>Jangkar Coffee</span>
          </a>
          <a href='#/' className='text-abu hover:text-tinta flex items-center gap-1.5 text-sm no-underline'>
            <ArrowLeft className='size-4' /> Beranda
          </a>
        </div>
      </header>

      <div className='mx-auto grid max-w-[1360px] gap-8 px-5 py-8 lg:grid-cols-[320px_minmax(0,1fr)]'>
        <aside className='lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:self-start lg:overflow-y-auto lg:pr-2'>
          <FormPreferensi
            p={p}
            ubah={ubah}
            berkas={berkas}
            setBerkas={setBerkas}
            foto={foto}
            setFoto={setFoto}
            kecamatan={kecamatan}
            sumber={meta?.sumber ?? null}
            onLokasiSaya={lokasiSaya}
            lokasiGalat={lokasiGalat}
          />
        </aside>

        <main className='min-w-0'>
          <p className='text-abu flex items-center gap-2.5 text-xs font-medium tracking-[0.22em] uppercase'>
            <span className='bg-aksen size-2 rounded-full' /> Sistem Pendukung Keputusan
          </p>
          <h1 className='mt-2 text-[clamp(2rem,4vw,3.2rem)] leading-[1.08] font-normal tracking-[-0.03em]'>
            Temukan kafe terbaik dengan Fuzzy <em className='text-aksen not-italic'>Tsukamoto.</em>
          </h1>

          {galat && (
            <div role='alert' className='mt-6 flex items-start gap-3 rounded-[20px] border border-red-200 bg-red-50 p-4 text-sm text-red-900'>
              <ServerOff className='mt-0.5 size-5 shrink-0' />
              <div>
                <p className='font-medium'>{galat}</p>
                <p className='mt-1 text-red-800/80'>
                  Nyalakan backend Python: <code className='rounded bg-white/70 px-1.5 py-0.5'>cd backend; uvicorn api:app --port 8000</code>
                </p>
              </div>
            </div>
          )}

          {hasil && !perluData && (
            <div className={memuat ? 'opacity-60 transition-opacity' : 'transition-opacity'} aria-busy={memuat}>
              <div className='mt-8 mb-3 flex items-center gap-3'>
                <h2 className='text-xl font-medium tracking-tight'>
                  {hasil.jumlah} kafe ditemukan
                  <span className='text-abu text-sm font-normal'> · {hasil.sumber} · mode {hasil.mode}</span>
                </h2>
                {memuat && <Loader2 className='text-abu size-4 animate-spin' aria-label='Menghitung' />}
              </div>

              {kafe.length ? (
                <>
                  <CarouselKafe kafe={kafe} aktif={pilih} onAktif={setPilih} />

                  <Judul>Tabel hasil</Judul>
                  <TabelHasil kafe={kafe} terpilih={pilih} onPilih={setPilih} />

                  <Judul>Peta</Judul>
                  <PetaKafe lat={p.lat} lng={p.lng} peta={hasil.peta} hasil={kafe} terpilih={pilih} onKlik={(lat, lng) => ubah({ lat, lng })} />
                  <p className='text-abu mt-2 text-xs'>Klik peta untuk memindahkan lokasimu. Oranye bernomor = rekomendasi, abu-abu = kafe lain di data.</p>

                  {terpilih && (
                    <>
                      <Judul>Perhitungan fuzzy</Judul>
                      <RincianFuzzy kafe={terpilih} />
                    </>
                  )}
                </>
              ) : (
                <div className='border-garis text-abu rounded-[20px] border bg-white p-8 text-center text-sm'>
                  Tidak ada kafe yang cocok. Coba perbesar jarak maksimum atau kurangi filter.
                </div>
              )}
            </div>
          )}

          {perluData && !galat && (
            <div className='border-garis mt-8 rounded-[20px] border bg-white p-8 text-center'>
              <Upload className='text-aksen mx-auto size-8' strokeWidth={1.6} />
              <p className='mt-3 text-lg font-medium'>Belum ada data kafe</p>
              <p className='text-abu mx-auto mt-1 max-w-md text-sm'>
                Unggah file Excel hasil scraping Google Maps (sheet <code>Data</code>) lewat panel di sebelah kiri. Foto kafe boleh diunggah sekalian.
              </p>
            </div>
          )}

          {!hasil && !galat && !perluData && (
            <div className='text-abu mt-10 flex items-center gap-2 text-sm'>
              <Loader2 className='size-4 animate-spin' /> Menghubungi backend Python…
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
