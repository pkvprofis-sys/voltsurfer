// Rechner auf der Startseite: liest die vorab simulierten Haushalte (rechner.json,
// erzeugt von scripts/precompute_rechner.py) und zeigt den gewählten Haushalt.
// Rechnet selbst nichts: jede Zahl stammt aus der Simulation mit echten Börsenpreisen.

const form = document.getElementById('calc');
const out = document.querySelector('.calc-out');
if (form && out) init();

async function init() {
  let data;
  try {
    const res = await fetch('rechner.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  } catch {
    return; // ohne Daten bleibt der Referenzhaushalt stehen, der im HTML steht
  }

  const fmt = new Intl.NumberFormat('de-DE');
  const el = (k) => out.querySelector(`[data-calc="${k}"]`);
  const bars = el('bars');
  const axis = el('axis');

  axis.innerHTML = data.monate.map((m) => `<span>${m}</span>`).join('');
  bars.innerHTML = data.monate.map((_, i) => `<div class="calc-bar" style="--i:${i}"><i></i><i></i></div>`).join('');
  const cols = [...bars.children];

  const years = (y) => (y == null ? null : Math.round(y));

  function show() {
    const f = new FormData(form);
    const key = `p${f.get('p')}-pv${f.get('pv') ? 1 : 0}-wp${f.get('wp') ? 1 : 0}-ea${f.get('ea') ? 1 : 0}-s${f.get('s')}`;
    const h = data.haushalte[key];
    if (!h) return;

    el('heute').textContent = `${fmt.format(h.heute.jahr_eur)} €`;
    el('verbund').textContent = `bis ${fmt.format(h.verbund.jahr_eur)} €`;
    const a = years(h.heute.amortisation_jahre), b = years(h.verbund.amortisation_jahre);
    const amort = a && b ? ` · rechnet sich in etwa ${a} Jahren, mit VPP in ${b}` : '';
    el('meta').textContent = `Strombedarf ${fmt.format(h.verbrauch_kwh)} kWh im Jahr${amort}`;

    const max = Math.max(1, ...h.verbund.monate_eur, ...h.heute.monate_eur);
    cols.forEach((col, i) => {
      const base = Math.max(0, h.heute.monate_eur[i]);
      const plus = Math.max(0, h.verbund.monate_eur[i] - base);
      col.children[0].style.height = `${(base / max) * 100}%`;
      col.children[1].style.height = `${(plus / max) * 100}%`;
      col.title = `${data.monate[i]}: ${fmt.format(base)} € ab dem ersten Tag, ${fmt.format(base + plus)} € mit VPP`;
    });
    el('chart').setAttribute('aria-label',
      `Ersparnis je Monat von September bis August: zusammen ${fmt.format(h.heute.jahr_eur)} Euro ab dem ersten Tag, ${fmt.format(h.verbund.jahr_eur)} Euro mit VPP`);
  }

  form.addEventListener('change', show);
  form.addEventListener('submit', (e) => e.preventDefault());
  show();
}
