import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Star } from 'lucide-react'
import { koma, urlFoto, type Kafe } from '@/lib/api'
import { cn } from '@/lib/utils'

const LEBAR_KARTU = 260

/** Kartu kafe yang bisa digeser (panah, seret, sentuh, keyboard). Kartu tengah membesar dan memuat tombol Buka dan Rute. */
export default function CarouselKafe({
  kafe,
  aktif,
  onAktif
}: {
  kafe: Kafe[]
  aktif: number
  onAktif: (i: number) => void
}) {
  const trek = useRef<HTMLDivElement>(null)
  const kartu = useRef<(HTMLDivElement | null)[]>([])
  const [cur, setCur] = useState(0)
  const geser = useRef({ turun: false, x0: 0, s0: 0, pindah: false })

  const pusatkan = useCallback((i: number, halus = true) => {
    const t = trek.current
    const c = kartu.current[Math.max(0, Math.min(kafe.length - 1, i))]
    if (!t || !c) return
    t.scrollTo({ left: c.offsetLeft - (t.clientWidth - c.offsetWidth) / 2, behavior: halus ? 'smooth' : 'auto' })
  }, [kafe.length])

  const perbarui = useCallback(() => {
    const t = trek.current
    if (!t) return
    const tengah = t.scrollLeft + t.clientWidth / 2
    let terbaik = 0
    let jarak = Infinity
    kartu.current.forEach((c, i) => {
      if (!c) return
      const d = Math.abs(c.offsetLeft + c.offsetWidth / 2 - tengah)
      if (d < jarak) {
        jarak = d
        terbaik = i
      }
    })
    setCur(terbaik)
    onAktif(terbaik)
  }, [onAktif])

  // Hasil baru → mulai dari kartu pertama.
  useEffect(() => {
    pusatkan(0, false)
    const id = setTimeout(perbarui, 60)
    return () => clearTimeout(id)
  }, [kafe, pusatkan, perbarui])

  // Dipilih dari luar (mis. klik baris tabel).
  useEffect(() => {
    if (aktif !== cur) pusatkan(aktif)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aktif])

  const mouseTurun = (e: React.PointerEvent) => {
    if (e.pointerType !== 'mouse' || !trek.current) return
    geser.current = { turun: true, x0: e.clientX, s0: trek.current.scrollLeft, pindah: false }
  }
  const mouseGerak = (e: React.PointerEvent) => {
    const g = geser.current
    if (!g.turun || !trek.current) return
    const dx = e.clientX - g.x0
    if (Math.abs(dx) > 4) {
      g.pindah = true
      trek.current.classList.add('cursor-grabbing', 'snap-none')
    }
    trek.current.scrollLeft = g.s0 - dx
  }
  const mouseNaik = () => {
    const g = geser.current
    if (!g.turun) return
    g.turun = false
    trek.current?.classList.remove('cursor-grabbing', 'snap-none')
    if (g.pindah) {
      pusatkan(cur)
      setTimeout(() => (geser.current.pindah = false), 0)
    }
  }

  if (!kafe.length) return null

  return (
    <div className='relative h-[470px] overflow-hidden rounded-[28px] bg-[radial-gradient(70%_90%_at_50%_45%,rgba(255,122,47,0.42),rgba(23,23,23,0)_70%)] bg-tinta'>
      <button
        type='button'
        aria-label='Kafe sebelumnya'
        disabled={cur === 0}
        onClick={() => pusatkan(cur - 1)}
        className='absolute top-1/2 left-3.5 z-10 flex size-10 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/15 text-white backdrop-blur hover:bg-white/30 disabled:cursor-default disabled:opacity-30'
      >
        <ChevronLeft className='size-5' />
      </button>
      <div
        ref={trek}
        tabIndex={0}
        aria-label='Rekomendasi kafe, geser untuk melihat lainnya'
        onScroll={() => requestAnimationFrame(perbarui)}
        onPointerDown={mouseTurun}
        onPointerMove={mouseGerak}
        onPointerUp={mouseNaik}
        onPointerLeave={mouseNaik}
        onKeyDown={e => {
          if (e.key === 'ArrowRight') (e.preventDefault(), pusatkan(cur + 1))
          if (e.key === 'ArrowLeft') (e.preventDefault(), pusatkan(cur - 1))
        }}
        style={{ paddingInline: `calc(50% - ${LEBAR_KARTU / 2}px)` }}
        className='relative flex h-full cursor-grab snap-x snap-mandatory items-center gap-[18px] overflow-x-auto outline-none [scrollbar-width:none] [&::-webkit-scrollbar]:hidden'
      >
        {kafe.map((k, i) => {
          const foto = urlFoto(k.foto)
          const on = i === cur
          return (
            <div
              key={`${k.nama}-${i}`}
              ref={el => {
                kartu.current[i] = el
              }}
              onClick={() => {
                if (!geser.current.pindah && !on) pusatkan(i)
              }}
              style={{ width: LEBAR_KARTU }}
              className={cn(
                'relative h-[400px] flex-none snap-center overflow-hidden rounded-[22px] bg-[#2a2a2a] text-white transition-[transform,opacity,box-shadow] duration-300',
                on ? 'scale-100 opacity-100 shadow-[0_18px_50px_rgba(0,0,0,0.55)]' : 'scale-[0.82] opacity-55 shadow-[0_10px_30px_rgba(0,0,0,0.35)]'
              )}
            >
              {foto ? (
                <img src={foto} alt={k.nama} draggable={false} className='pointer-events-none absolute inset-0 size-full object-cover' />
              ) : (
                <div className='pointer-events-none absolute inset-0 flex items-center justify-center bg-gradient-to-br from-aksen to-[#7a2d0b] text-[96px] font-medium'>
                  {k.nama.trim().charAt(0).toUpperCase()}
                </div>
              )}
              <div className='pointer-events-none absolute inset-0 bg-gradient-to-t from-black/90 via-black/35 via-45% to-transparent to-65%' />
              <span className='absolute top-3.5 left-3.5 rounded-full bg-aksen px-2.5 py-1 text-xs font-semibold text-tinta'>#{k.peringkat}</span>
              <span className='absolute top-3 right-4 flex items-center gap-1 text-[26px] font-medium tracking-tight'>
                {koma(k.rating)}
                <Star className='size-4 fill-white' />
              </span>
              <div className='absolute inset-x-4 bottom-4'>
                <p className='mb-2 line-clamp-2 text-[21px] leading-[1.15] font-medium tracking-tight'>{k.nama}</p>
                <div className='flex flex-wrap gap-x-3 gap-y-1 text-xs text-white/80'>
                  <span>{k.jenis}</span>
                  <span>{k.harga}</span>
                  <span>{koma(k.jarak_km)} km</span>
                </div>
                <div className='mt-2.5 h-[5px] overflow-hidden rounded-full bg-white/25'>
                  <div className='h-full rounded-full bg-aksen' style={{ width: `${Math.max(0, Math.min(100, k.skor))}%` }} />
                </div>
                <p className='mt-1.5 text-xs text-white/80'>Skor fuzzy {koma(k.skor)}</p>
                {on && (
                  <div className='mt-3 flex gap-2'>
                    <a
                      href={k.maps}
                      target='_blank'
                      rel='noopener'
                      onPointerDown={e => e.stopPropagation()}
                      className='flex-1 rounded-full bg-white/15 py-2 text-center text-[13px] font-medium text-white no-underline backdrop-blur hover:bg-white/25'
                    >
                      Buka
                    </a>
                    <a
                      href={k.rute}
                      target='_blank'
                      rel='noopener'
                      onPointerDown={e => e.stopPropagation()}
                      className='flex-1 rounded-full bg-aksen py-2 text-center text-[13px] font-medium text-tinta no-underline hover:brightness-105'
                    >
                      Rute
                    </a>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
      <button
        type='button'
        aria-label='Kafe berikutnya'
        disabled={cur === kafe.length - 1}
        onClick={() => pusatkan(cur + 1)}
        className='absolute top-1/2 right-3.5 z-10 flex size-10 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/15 text-white backdrop-blur hover:bg-white/30 disabled:cursor-default disabled:opacity-30'
      >
        <ChevronRight className='size-5' />
      </button>
    </div>
  )
}
