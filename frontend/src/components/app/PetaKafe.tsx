import { useEffect } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { Kafe, TitikPeta } from '@/lib/api'

function KlikPeta({ onKlik }: { onKlik: (lat: number, lng: number) => void }) {
  useMapEvents({ click: e => onKlik(+e.latlng.lat.toFixed(6), +e.latlng.lng.toFixed(6)) })
  return null
}

function Geser({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap()
  useEffect(() => {
    map.panTo([lat, lng], { animate: true })
  }, [lat, lng, map])
  return null
}

/** Peta OpenStreetMap: klik untuk memindahkan lokasimu. Oranye bernomor = rekomendasi, abu-abu = kafe lain di data. */
export default function PetaKafe({
  lat,
  lng,
  peta,
  hasil,
  terpilih,
  onKlik
}: {
  lat: number
  lng: number
  peta: TitikPeta[]
  hasil: Kafe[]
  terpilih: number
  onKlik: (lat: number, lng: number) => void
}) {
  return (
    <MapContainer center={[lat, lng]} zoom={13} scrollWheelZoom={false} className='border-garis h-[380px] w-full rounded-[20px] border'>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' />
      <KlikPeta onKlik={onKlik} />
      <Geser lat={lat} lng={lng} />
      {peta.map((t, i) => (
        <CircleMarker key={`${t.nama}-${i}`} center={[t.lat, t.lng]} radius={4} pathOptions={{ color: '#74716c', weight: 1, fillColor: '#74716c', fillOpacity: 0.6 }}>
          <Tooltip>{t.nama}</Tooltip>
        </CircleMarker>
      ))}
      {hasil.map((k, i) => (
        <CircleMarker
          key={`${k.nama}-${i}`}
          center={[k.lat, k.lng]}
          radius={i === terpilih ? 11 : 8}
          pathOptions={{ color: i === terpilih ? '#171717' : '#fff', weight: 2, fillColor: '#ff7a2f', fillOpacity: 1 }}
        >
          <Tooltip permanent={i === terpilih} direction='top'>
            #{k.peringkat} {k.nama}
          </Tooltip>
        </CircleMarker>
      ))}
      <CircleMarker center={[lat, lng]} radius={9} pathOptions={{ color: '#171717', weight: 3, fillColor: '#fff', fillOpacity: 1 }}>
        <Tooltip direction='bottom'>Lokasimu</Tooltip>
      </CircleMarker>
    </MapContainer>
  )
}
