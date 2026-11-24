import { lazy, Suspense, useEffect, useState } from 'react'
import CoreHero from '@/components/ui/syntra-hero'

// Halaman aplikasi (peta, carousel) dimuat saat dibutuhkan supaya beranda tetap ringan.
const AplikasiPage = lazy(() => import('@/pages/AplikasiPage'))

// Dua halaman, dipisah lewat hash supaya jalan di GitHub Pages tanpa pengaturan server:
//   #/     beranda
//   #/app  aplikasi rekomendasi (memanggil API Python)
const adaHalamanApp = () => window.location.hash.startsWith('#/app')

export default function Demo() {
  const [app, setApp] = useState(adaHalamanApp)
  useEffect(() => {
    const ubah = () => {
      setApp(adaHalamanApp())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', ubah)
    return () => window.removeEventListener('hashchange', ubah)
  }, [])

  return app ? (
    <Suspense fallback={<div className='min-h-screen bg-[#f8f7f3]' />}>
      <AplikasiPage />
    </Suspense>
  ) : (
    <CoreHero onStart={() => (window.location.hash = '#/app')} />
  )
}
