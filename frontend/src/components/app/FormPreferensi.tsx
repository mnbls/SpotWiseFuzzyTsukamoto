import { useEffect, useRef, useState } from 'react'
import { Crosshair, ImagePlus, Upload, X } from 'lucide-react'
import type { Param } from '@/lib/api'
import { cn } from '@/lib/utils'

const JENIS = ['Kedai Kopi', 'Kafe', 'Lainnya']

const kotak = 'border-garis w-full rounded-full border bg-white px-4 py-2 text-sm outline-none focus:border-aksen focus:ring-2 focus:ring-aksen/20'
const judul = 'text-abu mb-2.5 text-xs font-medium tracking-[0.14em] uppercase'

function Chip({ aktif, onClick, children }: { aktif: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type='button'
      aria-pressed={aktif}
      onClick={onClick}
      className={cn(
        'cursor-pointer rounded-full border px-3.5 py-1.5 text-[13px] transition-colors',
        aktif ? 'border-tinta bg-tinta text-white' : 'border-garis bg-white hover:border-tinta'
      )}
    >
      {children}
    </button>
  )
}

/** Kolom angka yang boleh diketik bebas ("-7." tetap tampil); nilai dikirim ke atas hanya bila sudah angka sah. */
function KolomAngka({ nilai, onUbah, min, maks }: { nilai: number; onUbah: (v: number) => void; min: number; maks: number }) {
  const [teks, setTeks] = useState(String(nilai))
  useEffect(() => {
    setTeks(t => (Number(t) === nilai ? t : String(nilai)))
  }, [nilai])
  return (
    <input
      className={cn(kotak, 'mt-1 text-tinta')}
      inputMode='decimal'
      value={teks}
      onChange={e => {
        setTeks(e.target.value)
        const v = Number(e.target.value)
        if (e.target.value.trim() !== '' && Number.isFinite(v) && v >= min && v <= maks) onUbah(v)
      }}
    />
  )
}

const alih = (daftar: string[], x: string) => (daftar.includes(x) ? daftar.filter(d => d !== x) : [...daftar, x])

export default function FormPreferensi({
  p,
  ubah,
  berkas,
  setBerkas,
  foto,
  setFoto,
  kecamatan,
  sumber,
  onLokasiSaya,
  lokasiGalat
}: {
  p: Param
  ubah: (b: Partial<Param>) => void
  berkas: File | null
  setBerkas: (f: File | null) => void
  foto: File[]
  setFoto: (f: File[]) => void
  kecamatan: string[]
  sumber: string | null
  onLokasiSaya: () => void
  lokasiGalat: string | null
}) {
  const inputBerkas = useRef<HTMLInputElement>(null)
  const inputFoto = useRef<HTMLInputElement>(null)

  return (
    <div className='flex flex-col gap-7'>
      <section>
        <p className={judul}>Data</p>
        <input
          ref={inputBerkas}
          type='file'
          accept='.xlsx'
          hidden
          onChange={e => {
            setBerkas(e.target.files?.[0] ?? null)
            e.target.value = ''
          }}
        />
        <button
          type='button'
          onClick={() => inputBerkas.current?.click()}
          className='border-garis hover:border-tinta flex w-full cursor-pointer items-center gap-2 rounded-full border bg-white px-4 py-2 text-left text-sm'
        >
          <Upload className='size-4 shrink-0' />
          <span className='truncate'>{berkas ? berkas.name : 'Unggah Excel (.xlsx)'}</span>
        </button>
        {berkas ? (
          <button type='button' onClick={() => setBerkas(null)} className='text-abu hover:text-tinta mt-2 flex cursor-pointer items-center gap-1 text-xs'>
            <X className='size-3.5' /> Pakai data bawaan
          </button>
        ) : (
          <p className='text-abu mt-2 text-xs'>{sumber ? `Data bawaan: ${sumber}` : 'Belum ada data bawaan, unggah file Excel.'}</p>
        )}

        <input
          ref={inputFoto}
          type='file'
          accept='image/jpeg,image/png,image/webp'
          multiple
          hidden
          onChange={e => {
            setFoto(Array.from(e.target.files ?? []))
            e.target.value = ''
          }}
        />
        <button
          type='button'
          onClick={() => inputFoto.current?.click()}
          className='border-garis hover:border-tinta mt-3 flex w-full cursor-pointer items-center gap-2 rounded-full border bg-white px-4 py-2 text-left text-sm'
        >
          <ImagePlus className='size-4 shrink-0' />
          <span className='truncate'>{foto.length ? `${foto.length} foto dipilih` : 'Unggah foto kafe (opsional)'}</span>
        </button>
        {foto.length > 0 && (
          <button type='button' onClick={() => setFoto([])} className='text-abu hover:text-tinta mt-2 flex cursor-pointer items-center gap-1 text-xs'>
            <X className='size-3.5' /> Hapus foto
          </button>
        )}
      </section>

      <section>
        <p className={judul}>Lokasi kamu</p>
        <div className='grid grid-cols-2 gap-2'>
          <label className='text-abu text-xs'>
            Latitude
            <KolomAngka nilai={p.lat} min={-90} maks={90} onUbah={lat => ubah({ lat })} />
          </label>
          <label className='text-abu text-xs'>
            Longitude
            <KolomAngka nilai={p.lng} min={-180} maks={180} onUbah={lng => ubah({ lng })} />
          </label>
        </div>
        <button
          type='button'
          onClick={onLokasiSaya}
          className='border-garis hover:border-tinta mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-full border bg-white px-4 py-2 text-sm'
        >
          <Crosshair className='size-4' /> Pakai lokasi saya
        </button>
        <p className='text-abu mt-2 text-xs'>{lokasiGalat ?? 'Atau klik peta di bawah untuk memilih titik.'}</p>
      </section>

      <section>
        <p className={judul}>Preferensi harga</p>
        <div className='border-garis grid grid-cols-2 gap-1 rounded-full border bg-white p-1' role='radiogroup' aria-label='Soal harga'>
          {[true, false].map(h => (
            <button
              key={String(h)}
              type='button'
              role='radio'
              aria-checked={p.hemat === h}
              onClick={() => ubah({ hemat: h })}
              className={cn('cursor-pointer rounded-full py-1.5 text-sm transition-colors', p.hemat === h ? 'bg-tinta text-white' : 'text-abu hover:text-tinta')}
            >
              {h ? 'Hemat' : 'Bebas'}
            </button>
          ))}
        </div>
        <p className='text-abu mt-2 text-xs'>{p.hemat ? 'Kafe mahal dinilai kurang baik.' : 'Harga tidak mengurangi skor.'}</p>
      </section>

      <section>
        <p className={judul}>Filter</p>
        <label className='text-abu flex items-center justify-between text-xs'>
          Jarak maksimum
          <b className='text-tinta text-sm font-medium'>{p.maks_km} km</b>
        </label>
        <input
          type='range'
          min={1}
          max={20}
          value={p.maks_km}
          onChange={e => ubah({ maks_km: Number(e.target.value) })}
          className='accent-aksen mt-1 mb-4 w-full'
          aria-label='Jarak maksimum (km)'
        />

        <p className='text-abu mb-2 text-xs'>Jenis</p>
        <div className='mb-4 flex flex-wrap gap-2'>
          {JENIS.map(j => (
            <Chip key={j} aktif={p.jenis.includes(j)} onClick={() => ubah({ jenis: alih(p.jenis, j) })}>
              {j}
            </Chip>
          ))}
        </div>

        {kecamatan.length > 1 && (
          <>
            <p className='text-abu mb-2 text-xs'>Kecamatan</p>
            <div className='mb-4 flex flex-wrap gap-2'>
              {kecamatan.map(k => (
                <Chip key={k} aktif={p.kecamatan.includes(k)} onClick={() => ubah({ kecamatan: alih(p.kecamatan, k) })}>
                  {k}
                </Chip>
              ))}
            </div>
          </>
        )}

        <label className='flex cursor-pointer items-center gap-2.5 text-sm'>
          <input type='checkbox' checked={p.hanya_24} onChange={e => ubah({ hanya_24: e.target.checked })} className='accent-aksen size-4' />
          Hanya yang buka 24 jam
        </label>
      </section>
    </div>
  )
}
