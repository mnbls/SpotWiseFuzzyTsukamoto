import type { Kafe } from '@/lib/api'
import { koma } from '@/lib/api'

const f3 = (v: number) => v.toFixed(3).replace('.', ',')

/** Langkah perhitungan fuzzy Tsukamoto satu kafe. Semua angka dihitung di backend Python. */
export default function RincianFuzzy({ kafe }: { kafe: Kafe }) {
  const { fuzzifikasi: f, aturan, z_akhir } = kafe.perhitungan
  const chip = (nama: string, nilai: number) => (
    <span key={nama} className='border-garis rounded-full border bg-white px-3 py-1 text-[13px]'>
      {nama} <b className='font-semibold tabular-nums'>{f3(nilai)}</b>
    </span>
  )
  return (
    <div className='border-garis rounded-[20px] border bg-white p-5'>
      <p className='text-[15px] font-medium'>
        {kafe.nama} <span className='text-abu font-normal'>· jarak {koma(kafe.jarak_km, 2)} km · rating {koma(kafe.rating)}</span>
      </p>

      <p className='text-abu mt-4 mb-2 text-xs font-medium tracking-[0.14em] uppercase'>1. Fuzzifikasi</p>
      <div className='flex flex-wrap gap-2'>
        {chip('Dekat', f.dekat)}
        {chip('Jauh', f.jauh)}
        {chip('Rating tinggi', f.rating_tinggi)}
        {chip('Rating rendah', f.rating_rendah)}
        {chip('Murah', f.murah)}
        {chip('Sedang', f.sedang)}
        {chip('Mahal', f.mahal)}
      </div>

      <p className='text-abu mt-5 mb-2 text-xs font-medium tracking-[0.14em] uppercase'>2. Inferensi (AND = min)</p>
      <div className='overflow-x-auto'>
        <table className='w-full border-collapse text-sm'>
          <thead>
            <tr className='text-abu border-garis border-b text-left'>
              <th className='py-2 pr-3 font-medium'>Aturan</th>
              <th className='px-3 py-2 text-right font-medium'>α</th>
              <th className='px-3 py-2 text-right font-medium'>z</th>
              <th className='py-2 pl-3 text-right font-medium'>α × z</th>
            </tr>
          </thead>
          <tbody>
            {aturan.map(a => (
              <tr key={a.aturan} className='border-garis border-b last:border-0'>
                <td className='py-2 pr-3'>{a.aturan}</td>
                <td className='px-3 py-2 text-right tabular-nums'>{f3(a.alpha)}</td>
                <td className='px-3 py-2 text-right tabular-nums'>{koma(a.z, 2)}</td>
                <td className='py-2 pl-3 text-right tabular-nums'>{koma(a.alpha_z, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className='text-abu mt-5 mb-1 text-xs font-medium tracking-[0.14em] uppercase'>3. Defuzzifikasi</p>
      <p className='text-sm'>
        z = Σ(α·z) / Σα = <b className='text-aksen text-lg font-semibold'>{koma(z_akhir, 2)}</b>
      </p>
    </div>
  )
}
