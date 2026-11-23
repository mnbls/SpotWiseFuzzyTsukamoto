"""Tabel hasil: kolom bisa diurut (klik header) dan diubah lebarnya (tarik tepi kolom)."""
import json

import streamlit as st

# (kunci data, judul, lebar awal px, rata kanan)
KOLOM = [
    ("nama_maps", "Nama tempat", 260, False),
    ("kecamatan", "Kecamatan", 140, False),
    ("harga_label", "Harga", 120, False),
    ("rating", "Rating", 90, True),
    ("jarak_km", "Jarak (km)", 110, True),
    ("skor", "Skor", 190, True),
    ("link_maps", "Peta", 80, False),
    ("link_rute", "Rute", 80, False),
]

_HTML = """
<style>
  :root { --ink:#171717; --muted:#74716c; --line:#d9d6d0; --accent:#ff7a2f; --head:rgba(239,237,230,.6); }
  * { box-sizing: border-box; }
  body { margin:0; font-family:'Onest',system-ui,sans-serif; color:var(--ink); background:transparent; }
  .wrap { border:1px solid var(--line); border-radius:20px; background:#fff; overflow:auto; max-height:__MAXH__px; }
  table { border-collapse:collapse; table-layout:fixed; font-size:14px; }
  th { position:sticky; top:0; z-index:2; height:40px; padding:0 12px; text-align:left; font-weight:500;
       color:var(--muted); background:#efede6; border-bottom:1px solid var(--line); user-select:none; }
  th .in { display:flex; align-items:center; justify-content:space-between; gap:8px; height:100%; cursor:pointer; }
  th.r .in { flex-direction:row-reverse; justify-content:flex-start; }
  th:focus-visible .in, th .in:focus-visible { outline:2px solid var(--accent); outline-offset:-2px; border-radius:6px; }
  th .t { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  th svg { flex:none; opacity:.6; }
  .rs { position:absolute; top:0; right:-8px; width:16px; height:100%; cursor:col-resize; z-index:3; touch-action:none; }
  .rs::before { content:""; position:absolute; top:0; bottom:0; left:50%; width:1px; background:var(--line); }
  th:last-child .rs { display:none; }
  td { padding:12px; border-bottom:1px solid var(--line); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:middle; }
  tr:last-child td { border-bottom:0; }
  tbody tr { transition:background .15s; }
  tbody tr:hover { background:rgba(239,237,230,.5); }
  tbody tr.go { cursor:pointer; }
  td.r { text-align:right; font-variant-numeric:tabular-nums; }
  td.n { font-weight:500; }
  .sk { display:flex; align-items:center; gap:10px; }
  .sk i { flex:1; height:8px; border-radius:99px; background:#efede6; overflow:hidden; }
  .sk i b { display:block; height:100%; background:var(--accent); border-radius:99px; }
  .sk span { width:38px; text-align:right; }
  a { color:var(--accent); font-weight:500; text-decoration:none; }
  a:hover { text-decoration:underline; }
  .empty { height:96px; text-align:center; color:var(--muted); }
  p.cap { margin:10px 0 0; text-align:center; font-size:13px; color:var(--muted); }
</style>
<div class="wrap"><table id="t"></table></div>
<p class="cap">Klik baris untuk membuka tempatnya di Google Maps, atau "Rute" untuk petunjuk arah. Klik judul kolom untuk mengurutkan. Tarik tepi kolom untuk mengubah lebar (klik dua kali untuk mengembalikan).</p>
<script>
const COLS = __COLS__, ROWS = __ROWS__;
const UP = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>';
const DOWN = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>';
const widths = COLS.map(c => c.w);
let sortKey = 'skor', sortDesc = true;
const el = document.getElementById('t');

function safeUrl(u) { try { const x = new URL(u); return /^https?:$/.test(x.protocol) ? x.href : null; } catch { return null; } }
function cmp(a, b) {
  const x = a[sortKey], y = b[sortKey];
  if (x == null || x === '') return 1;           // kosong selalu di bawah
  if (y == null || y === '') return -1;
  const r = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'id');
  return sortDesc ? -r : r;
}
function fmt(k, v) {
  if (v == null || v === '') return '–';
  if (k === 'jarak_km') return v.toFixed(2).replace('.', ',');
  if (k === 'rating') return String(v).replace('.', ',');
  return v;
}
function render() {
  const rows = [...ROWS].sort(cmp);
  el.style.width = widths.reduce((a, b) => a + b, 0) + 'px';
  el.textContent = '';
  const cg = document.createElement('colgroup');
  widths.forEach(w => { const c = document.createElement('col'); c.style.width = w + 'px'; cg.appendChild(c); });
  el.appendChild(cg);
  const thead = el.createTHead(), hr = thead.insertRow();
  COLS.forEach((c, i) => {
    const th = document.createElement('th');
    th.className = c.r ? 'r' : '';
    th.setAttribute('aria-sort', sortKey === c.k ? (sortDesc ? 'descending' : 'ascending') : 'none');
    const inn = document.createElement('div'); inn.className = 'in'; inn.tabIndex = 0;
    const t = document.createElement('span'); t.className = 't'; t.textContent = c.t;
    inn.appendChild(t);
    if (sortKey === c.k) { const s = document.createElement('span'); s.innerHTML = sortDesc ? DOWN : UP; inn.appendChild(s.firstChild); }
    const toggle = () => { if (sortKey === c.k) sortDesc = !sortDesc; else { sortKey = c.k; sortDesc = c.r; } render(); };
    inn.onclick = toggle;
    inn.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } };
    th.appendChild(inn);
    const rs = document.createElement('div'); rs.className = 'rs';
    rs.ondblclick = () => { widths[i] = c.w; render(); };
    rs.onpointerdown = e => {
      e.preventDefault(); rs.setPointerCapture(e.pointerId);
      const x0 = e.clientX, w0 = widths[i];
      rs.onpointermove = m => {
        widths[i] = Math.max(60, w0 + m.clientX - x0);
        el.style.width = widths.reduce((a, b) => a + b, 0) + 'px';
        cg.children[i].style.width = widths[i] + 'px';
      };
      rs.onpointerup = () => { rs.onpointermove = null; rs.onpointerup = null; };
    };
    th.style.position = 'sticky'; th.appendChild(rs);
    hr.appendChild(th);
  });
  const tb = el.createTBody();
  if (!rows.length) {
    const td = tb.insertRow().insertCell(); td.colSpan = COLS.length; td.className = 'empty'; td.textContent = 'Tidak ada hasil.';
  }
  rows.forEach(r => {
    const tr = tb.insertRow();
    const buka = safeUrl(r.link_maps);
    if (buka) {
      tr.className = 'go'; tr.title = 'Klik untuk membuka di Google Maps';
      tr.onclick = e => { if (!e.target.closest('a')) window.open(buka, '_blank', 'noopener'); };
    }
    COLS.forEach(c => {
      const td = tr.insertCell(); const v = r[c.k];
      if (c.r) td.className = 'r';
      if (c.k === 'nama_maps') { td.className = 'n'; td.textContent = v; td.title = v; }
      else if (c.k === 'skor') {
        td.className = 'r';
        td.innerHTML = '<div class="sk"><i><b></b></i><span></span></div>';
        td.querySelector('b').style.width = Math.max(0, Math.min(100, v)) + '%';
        td.querySelector('span').textContent = v.toFixed(1).replace('.', ',');
      } else if (c.k === 'link_maps' || c.k === 'link_rute') {
        const u = safeUrl(v);
        if (u) { const a = document.createElement('a'); a.href = u; a.target = '_blank'; a.rel = 'noopener'; a.textContent = c.k === 'link_rute' ? 'Rute' : 'Buka'; td.appendChild(a); }
        else td.textContent = '–';
      } else { td.textContent = fmt(c.k, v); td.title = td.textContent; }
    });
  });
}
render();
</script>
"""


def tabel_hasil(df, maks_tinggi=520):
    """Tampilkan df (kolom di KOLOM) sebagai tabel yang bisa diurut dan diubah lebar kolomnya."""
    baris = []
    for r in df[[k for k, *_ in KOLOM]].itertuples(index=False):
        d = {}
        for (k, *_), v in zip(KOLOM, r):
            d[k] = None if v != v else (v if isinstance(v, str) else float(v))
        baris.append(d)
    kolom = [{"k": k, "t": t, "w": w, "r": r} for k, t, w, r in KOLOM]

    def js(obj):  # aman di dalam <script>: "</" tidak boleh muncul
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    html = _HTML.replace("__COLS__", js(kolom)).replace("__ROWS__", js(baris)).replace("__MAXH__", str(maks_tinggi))
    tinggi = maks_tinggi + 70
    if hasattr(st, "iframe"):
        st.iframe(html, height=tinggi)
    else:  # Streamlit lama
        import streamlit.components.v1 as components

        components.html(html, height=tinggi, scrolling=False)
