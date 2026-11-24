"""Carousel kartu kafe yang bisa digeser: kartu tengah membesar, foto dari kolom `foto`."""
import base64
import json
import mimetypes
from pathlib import Path

import streamlit as st

_HTML = """
<style>
  * { box-sizing: border-box; }
  body { margin:0; font-family:'Onest',system-ui,sans-serif; color:#fff; background:transparent; }
  .stage { position:relative; border-radius:28px; overflow:hidden; height:__H__px;
    background: radial-gradient(70% 90% at 50% 45%, rgba(255,122,47,.42), rgba(23,23,23,0) 70%), #171717; }
  .track { display:flex; align-items:center; gap:18px; height:100%; overflow-x:auto; scroll-snap-type:x mandatory;
    scrollbar-width:none; padding:0 calc(50% - 130px); cursor:grab; -webkit-overflow-scrolling:touch; }
  .track::-webkit-scrollbar { display:none; }
  .track.drag { cursor:grabbing; scroll-snap-type:none; user-select:none; }
  .card { position:relative; flex:none; width:260px; height:__CH__px; border-radius:22px; overflow:hidden;
    scroll-snap-align:center; background:#2a2a2a; transform:scale(.82); opacity:.55;
    transition:transform .35s cubic-bezier(.22,1,.36,1), opacity .35s, box-shadow .35s; box-shadow:0 10px 30px rgba(0,0,0,.35); }
  .card.on { transform:scale(1); opacity:1; box-shadow:0 18px 50px rgba(0,0,0,.55); }
  .card img, .card .ph { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; pointer-events:none; }
  .card .ph { display:flex; align-items:center; justify-content:center; font-size:96px; font-weight:500;
    color:rgba(255,255,255,.9); background:linear-gradient(160deg,#ff7a2f,#7a2d0b); }
  .card::after { content:""; position:absolute; inset:0; pointer-events:none;
    background:linear-gradient(to top, rgba(0,0,0,.88) 0%, rgba(0,0,0,.35) 42%, rgba(0,0,0,0) 62%); }
  .rank { position:absolute; z-index:2; top:14px; left:14px; padding:4px 10px; border-radius:99px; font-size:12px; font-weight:600;
    background:#ff7a2f; color:#171717; }
  .rate { position:absolute; z-index:2; top:12px; right:16px; font-size:26px; font-weight:500; letter-spacing:-.03em; }
  .rate small { font-size:15px; opacity:.85; margin-left:2px; }
  .info { position:absolute; z-index:2; left:16px; right:16px; bottom:16px; }
  .nm { font-size:21px; line-height:1.15; font-weight:500; letter-spacing:-.02em; margin:0 0 8px;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .mt { font-size:12px; color:rgba(255,255,255,.78); display:flex; flex-wrap:wrap; gap:4px 12px; }
  .bar { height:5px; border-radius:99px; background:rgba(255,255,255,.25); overflow:hidden; margin:10px 0 0; }
  .bar b { display:block; height:100%; background:#ff7a2f; border-radius:99px; }
  .act { display:none; gap:8px; margin-top:12px; }
  .card.on .act { display:flex; }
  .act a { flex:1; text-align:center; padding:8px 0; border-radius:99px; font-size:13px; font-weight:500;
    text-decoration:none; background:rgba(255,255,255,.16); color:#fff; backdrop-filter:blur(6px); }
  .act a.p { background:#ff7a2f; color:#171717; }
  .nav { position:absolute; top:50%; z-index:5; width:40px; height:40px; margin-top:-20px; border:0; border-radius:50%;
    background:rgba(255,255,255,.14); color:#fff; cursor:pointer; backdrop-filter:blur(6px); display:flex; align-items:center; justify-content:center; }
  .nav:hover { background:rgba(255,255,255,.28); }
  .nav.l { left:14px; } .nav.r { right:14px; }
  .nav:disabled { opacity:.3; cursor:default; }
  .hint { position:absolute; z-index:5; left:0; right:0; bottom:10px; text-align:center; font-size:11px; color:rgba(255,255,255,.55); pointer-events:none; }
</style>
<div class="stage">
  <button class="nav l" id="pv" aria-label="Sebelumnya"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>
  <div class="track" id="tr" tabindex="0" aria-label="Rekomendasi kafe, geser untuk melihat lainnya"></div>
  <button class="nav r" id="nx" aria-label="Berikutnya"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></button>
</div>
<script>
const ITEMS = __ITEMS__;
const tr = document.getElementById('tr'), pv = document.getElementById('pv'), nx = document.getElementById('nx');
function safeUrl(u) { try { const x = new URL(u); return /^https?:$/.test(x.protocol) ? x.href : null; } catch { return null; } }
const fmt = (v, d) => v == null ? '–' : v.toFixed(d).replace('.', ',');
ITEMS.forEach((it, i) => {
  const c = document.createElement('div'); c.className = 'card';
  const media = it.foto ? Object.assign(document.createElement('img'), { src: it.foto, alt: '', draggable: false })
                        : Object.assign(document.createElement('div'), { className: 'ph', textContent: (it.nama || '?').trim().charAt(0).toUpperCase() });
  c.appendChild(media);
  const rank = document.createElement('div'); rank.className = 'rank'; rank.textContent = '#' + (i + 1); c.appendChild(rank);
  const rate = document.createElement('div'); rate.className = 'rate'; rate.innerHTML = fmt(it.rating, 1) + '<small>★</small>'; c.appendChild(rate);
  const info = document.createElement('div'); info.className = 'info';
  const nm = document.createElement('p'); nm.className = 'nm'; nm.textContent = it.nama; info.appendChild(nm);
  const mt = document.createElement('div'); mt.className = 'mt';
  [it.jenis, it.harga, fmt(it.jarak, 1) + ' km'].forEach(t => { if (t) { const s = document.createElement('span'); s.textContent = t; mt.appendChild(s); } });
  info.appendChild(mt);
  const bar = document.createElement('div'); bar.className = 'bar'; const b = document.createElement('b');
  b.style.width = Math.max(0, Math.min(100, it.skor)) + '%'; bar.appendChild(b); info.appendChild(bar);
  const sk = document.createElement('div'); sk.className = 'mt'; sk.style.marginTop = '6px'; sk.textContent = 'Skor fuzzy ' + fmt(it.skor, 1); info.appendChild(sk);
  const act = document.createElement('div'); act.className = 'act';
  [['Buka', it.maps, ''], ['Rute', it.rute, 'p']].forEach(([t, u, k]) => {
    const url = safeUrl(u); if (!url) return;
    const a = document.createElement('a'); a.href = url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = t; a.className = k;
    a.addEventListener('pointerdown', e => e.stopPropagation()); act.appendChild(a);
  });
  info.appendChild(act); c.appendChild(info);
  c.addEventListener('click', () => { if (moved) return; if (!c.classList.contains('on')) center(i); });
  tr.appendChild(c);
});
const cards = [...tr.children];
let cur = 0, moved = false;
function center(i, smooth = true) {
  i = Math.max(0, Math.min(cards.length - 1, i));
  const c = cards[i];
  tr.scrollTo({ left: c.offsetLeft - (tr.clientWidth - c.offsetWidth) / 2, behavior: smooth ? 'smooth' : 'auto' });
}
function update() {
  const mid = tr.scrollLeft + tr.clientWidth / 2; let best = 0, bd = 1e9;
  cards.forEach((c, i) => { const d = Math.abs(c.offsetLeft + c.offsetWidth / 2 - mid); if (d < bd) { bd = d; best = i; } });
  cur = best; cards.forEach((c, i) => c.classList.toggle('on', i === best));
  pv.disabled = best === 0; nx.disabled = best === cards.length - 1;
}
tr.addEventListener('scroll', () => requestAnimationFrame(update));
pv.onclick = () => center(cur - 1); nx.onclick = () => center(cur + 1);
tr.addEventListener('keydown', e => { if (e.key === 'ArrowRight') { e.preventDefault(); center(cur + 1); } if (e.key === 'ArrowLeft') { e.preventDefault(); center(cur - 1); } });
// geser dengan mouse (sentuh sudah bawaan browser)
let down = false, x0 = 0, s0 = 0;
tr.addEventListener('pointerdown', e => { if (e.pointerType !== 'mouse') return; down = true; moved = false; x0 = e.clientX; s0 = tr.scrollLeft; });
window.addEventListener('pointermove', e => { if (!down) return; const dx = e.clientX - x0; if (Math.abs(dx) > 4) { moved = true; tr.classList.add('drag'); } tr.scrollLeft = s0 - dx; });
window.addEventListener('pointerup', () => { if (!down) return; down = false; tr.classList.remove('drag'); if (moved) { center(cur); setTimeout(() => moved = false, 0); } });
update(); center(0, false); setTimeout(update, 50);
</script>
"""


def foto_uri(nama_file, folder_foto, unggahan):
    """Ubah nama file foto jadi data-URI. Mengembalikan URL apa adanya bila sudah http(s)."""
    if not isinstance(nama_file, str) or not nama_file.strip():
        return None
    nama_file = nama_file.strip()
    if nama_file.startswith(("http://", "https://")):
        return nama_file
    if nama_file in unggahan:
        data, tipe = unggahan[nama_file]
    else:
        p = next((Path(d) / nama_file for d in folder_foto if (Path(d) / nama_file).is_file()), None)
        if p is None:
            return None
        data, tipe = p.read_bytes(), mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{tipe};base64," + base64.b64encode(data).decode()


def carousel_kafe(items, tinggi=460):
    """items: list dict {nama, foto, rating, jenis, harga, jarak, skor, maps, rute}."""
    kartu = tinggi - 60
    js = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    html = _HTML.replace("__ITEMS__", js).replace("__H__", str(tinggi)).replace("__CH__", str(kartu))
    if hasattr(st, "iframe"):
        st.iframe(html, height=tinggi + 8)
    else:
        import streamlit.components.v1 as components

        components.html(html, height=tinggi + 8, scrolling=False)
