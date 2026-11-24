import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { koma, type Kafe } from '@/lib/api'
import { cn } from '@/lib/utils'

type Kunci = 'nama' | 'kecamatan' | 'harga' | 'rating' | 'jarak_km' | 'skor'

// w = lebar awal (px). Kolom terakhir ("Peta") tidak bisa diurutkan.
const KOLOM: { k: Kunci | 'peta'; t: string; w: number; kanan?: boolean }[] = [
  { k: 'nama', t: 'Nama kafe', w: 260 },
  { k: 'kecamatan', t: 'Kecamatan', w: 130 },
  { k: 'harga', t: 'Harga', w: 120 },
  { k: 'rating', t: 'Rating', w: 90, kanan: true },
  { k: 'jarak_km', t: 'Jarak (km)', w: 110, kanan: true },
  { k: 'skor', t: 'Skor', w: 190, kanan: true },
  { k: 'peta', t: 'Peta', w: 110 }
]
const LEBAR_MIN = 60

/**
 * Tabel hasil: klik judul kolom untuk mengurutkan, tarik tepi kolom untuk mengubah lebar
 * (klik dua kali untuk mengembalikan), klik baris untuk memilih kafe.
 */
export default function TabelHasil({
  kafe,
  terpilih,
  onPilih
}: {
  kafe: Kafe[]
  terpilih: number
  onPilih: (i: number) => void
}) {
  const [kunci, setKunci] = useState<Kunci>('skor')
  const [turun, setTurun] = useState(true)
  const [lebar, setLebar] = useState(() => KOLOM.map(c => c.w))

  const baris = useMemo(() => {
    const dengan = kafe.map((k, i) => ({ k, i }))
    return dengan.sort((a, b) => {
      const x = a.k[kunci]
      const y = b.k[kunci]
      const r = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'id')
      return turun ? -r : r
    })
  }, [kafe, kunci, turun])

  const urut = (k: Kunci, kanan?: boolean) => {
    if (kunci === k) setTurun(!turun)
    else {
      setKunci(k)
      setTurun(!!kanan)
    }
  }

  const ubahLebar = (i: number, w: number) => setLebar(l => l.map((x, j) => (j === i ? Math.max(LEBAR_MIN, Math.round(w)) : x)))

  const mulaiTarik = (e: React.PointerEvent<HTMLDivElement>, i: number) => {
    e.preventDefault()
    e.stopPropagation()
    const el = e.currentTarget
    el.setPointerCapture(e.pointerId)
    const x0 = e.clientX
    const w0 = lebar[i]
    el.onpointermove = m => ubahLebar(i, w0 + m.clientX - x0)
    el.onpointerup = () => {
      el.onpointermove = null
      el.onpointerup = null
    }
  }

  return (
    <div className='border-garis max-h-[480px] overflow-auto rounded-[20px] border bg-white'>
      <table className='border-collapse text-sm' style={{ tableLayout: 'fixed', width: lebar.reduce((a, b) => a + b, 0) }}>
        <colgroup>
          {lebar.map((w, i) => (
            <col key={i} style={{ width: w }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {KOLOM.map((c, i) => {
              const dapatUrut = c.k !== 'peta'
              return (
                <th
                  key={c.k}
                  aria-sort={c.k === kunci ? (turun ? 'descending' : 'ascending') : 'none'}
                  className='bg-panel text-abu border-garis sticky top-0 z-[1] h-10 border-b px-3 text-left font-medium'
                >
                  {dapatUrut ? (
                    <button
                      type='button'
                      onClick={() => urut(c.k as Kunci, c.kanan)}
                      className={cn('flex h-10 w-full cursor-pointer items-center gap-2 select-none', c.kanan ? 'flex-row-reverse justify-start' : 'justify-between')}
                    >
                      <span className='truncate'>{c.t}</span>
                      {c.k === kunci && (turun ? <ChevronDown className='size-4 shrink-0 opacity-60' /> : <ChevronUp className='size-4 shrink-0 opacity-60' />)}
                    </button>
                  ) : (
                    <span>{c.t}</span>
                  )}
                  {i < KOLOM.length - 1 && (
                    <div
                      role='separator'
                      aria-orientation='vertical'
                      aria-label={`Ubah lebar kolom ${c.t}`}
                      title='Tarik untuk mengubah lebar, klik dua kali untuk mengembalikan'
                      onPointerDown={e => mulaiTarik(e, i)}
                      onDoubleClick={() => ubahLebar(i, c.w)}
                      className='group absolute top-0 -right-2 z-[2] h-full w-4 cursor-col-resize touch-none'
                    >
                      <span className='bg-garis group-hover:bg-aksen absolute inset-y-0 left-1/2 w-px group-hover:w-0.5' />
                    </div>
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {baris.map(({ k, i }) => (
            <tr
              key={`${k.nama}-${i}`}
              onClick={() => onPilih(i)}
              className={cn('border-garis hover:bg-panel/50 cursor-pointer border-b transition-colors last:border-0', i === terpilih && 'bg-aksen/10')}
            >
              <td className='truncate px-3 py-3 font-medium' title={k.nama}>
                {k.nama}
              </td>
              <td className='truncate px-3 py-3'>{k.kecamatan}</td>
              <td className='truncate px-3 py-3'>{k.harga}</td>
              <td className='px-3 py-3 text-right tabular-nums'>{koma(k.rating)}</td>
              <td className='px-3 py-3 text-right tabular-nums'>{koma(k.jarak_km, 2)}</td>
              <td className='px-3 py-3'>
                <div className='flex items-center gap-2.5'>
                  <div className='bg-panel h-2 flex-1 overflow-hidden rounded-full'>
                    <div className='bg-aksen h-full rounded-full' style={{ width: `${Math.max(0, Math.min(100, k.skor))}%` }} />
                  </div>
                  <span className='w-10 text-right tabular-nums'>{koma(k.skor)}</span>
                </div>
              </td>
              <td className='truncate px-3 py-3'>
                <a href={k.maps} target='_blank' rel='noopener' onClick={e => e.stopPropagation()} className='text-aksen font-medium no-underline hover:underline'>
                  Buka
                </a>
                <span className='text-garis mx-1.5'>|</span>
                <a href={k.rute} target='_blank' rel='noopener' onClick={e => e.stopPropagation()} className='text-aksen font-medium no-underline hover:underline'>
                  Rute
                </a>
              </td>
            </tr>
          ))}
          {!baris.length && (
            <tr>
              <td colSpan={KOLOM.length} className='text-abu h-24 text-center'>
                Tidak ada hasil.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
