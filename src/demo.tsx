import CoreHero from '@/components/ui/syntra-hero'

// Alamat aplikasi Python (Streamlit). Ganti setelah deploy di share.streamlit.io.
const APP_URL = import.meta.env.VITE_APP_URL ?? 'https://spotwise-fuzzy-tsukamoto.streamlit.app'

export default function Demo() {
  return <CoreHero onStart={() => window.location.assign(APP_URL)} />
}
