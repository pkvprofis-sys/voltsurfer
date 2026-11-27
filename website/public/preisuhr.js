// Preisuhr: In den Börsenpreis-Karten (Sommertag im Plan, Wintertag im Markt-Abschnitt) läuft die Zahl
// Stunde für Stunde durch den Tag und der passende Balken leuchtet. Die Werte sind die echten
// Stundenmittel aus data-values; am Tiefst- und Höchstpreis bleibt die Uhr kurz stehen.
// Mit reduzierter Bewegung bleibt der Tiefstpreis stehen.

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const fmt = (v) => `${v.toLocaleString('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ct`;

document.querySelectorAll('.ui-stat[data-uhr]').forEach((stat) => {
  const vals = stat.dataset.values.split(',').map(Number);
  const num = stat.querySelector('[data-stat-num]');
  const sub = stat.querySelector('.ui-stat__sub');
  const min = vals.indexOf(Math.min(...vals));
  const max = vals.indexOf(Math.max(...vals));

  const show = (h) => {
    num.textContent = fmt(vals[h]);
    sub.textContent = `um ${h} Uhr${h === min ? ' · Tiefstpreis' : h === max ? ' · Höchstpreis' : ''}`;
    // die Balken baut das Stat-Fragment selbst, deshalb jedes Mal frisch suchen
    stat.querySelectorAll('.ui-stat__bars rect').forEach((r, i) => r.classList.toggle('is-now', i === h));
  };

  let h = 0;
  let timer = null;
  const tick = () => {
    show(h);
    const wait = h === min || h === max ? 2200 : 650;
    h = (h + 1) % vals.length;
    timer = setTimeout(tick, wait);
  };

  new IntersectionObserver(([e]) => {
    if (reduce) {
      if (e.isIntersecting) setTimeout(() => show(min), 300);
      return;
    }
    if (e.isIntersecting && !timer) tick();
    if (!e.isIntersecting && timer) { clearTimeout(timer); timer = null; }
  }).observe(stat);
});
