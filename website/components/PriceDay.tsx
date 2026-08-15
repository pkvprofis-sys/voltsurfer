"use client";

import { useEffect, useRef, useState } from "react";

import { ABENDSPITZE, PROFIL_JAHR, SAISON, type Saison } from "@/lib/preise";

const B = 760;
const H = 380;
const PAD = { oben: 52, rechts: 24, unten: 50, links: 52 };
const CT_MAX = 21;
const CT_MIN = -3;

const x = (stunde: number) => PAD.links + (stunde / 24) * (B - PAD.links - PAD.rechts);
const y = (ct: number) =>
  PAD.oben + ((CT_MAX - ct) / (CT_MAX - CT_MIN)) * (H - PAD.oben - PAD.unten);

/** Weiche Kurve durch die 24 Stundenpunkte (Catmull-Rom als Bézier). */
function pfad(werte: number[]) {
  const p = werte.map((ct, h) => [x(h + 0.5), y(ct)] as const);
  let d = `M ${p[0][0]} ${p[0][1]}`;
  for (let i = 0; i < p.length - 1; i++) {
    const v = p[i === 0 ? 0 : i - 1];
    const a = p[i];
    const b = p[i + 1];
    const n = p[i + 2] ?? b;
    d += ` C ${a[0] + (b[0] - v[0]) / 6} ${a[1] + (b[1] - v[1]) / 6}, ${
      b[0] - (n[0] - a[0]) / 6
    } ${b[1] - (n[1] - a[1]) / 6}, ${b[0]} ${b[1]}`;
  }
  return d;
}

export function PriceDay() {
  // Sommer als Standard — im Winter zeigen wir den Wintertag zuerst
  const [saison, setSaison] = useState<Saison>("sommer");
  const [werte, setWerte] = useState<number[]>([...SAISON.sommer.profil]);
  const anim = useRef<number | null>(null);

  useEffect(() => {
    const monat = new Date().getMonth(); // 0 = Januar
    if (monat >= 9 || monat <= 1) {
      setSaison("winter");
      setWerte([...SAISON.winter.profil]);
    }
  }, []);

  function wechseln(neu: Saison) {
    if (neu === saison) return;
    setSaison(neu);

    const ziel = SAISON[neu].profil;
    const start = [...werte];
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setWerte([...ziel]);
      return;
    }

    if (anim.current) cancelAnimationFrame(anim.current);
    const t0 = performance.now();
    const dauer = 480;
    const schritt = (jetzt: number) => {
      const p = Math.min(1, (jetzt - t0) / dauer);
      const e = 1 - Math.pow(1 - p, 3); // ease-out
      setWerte(start.map((v, i) => v + (ziel[i] - v) * e));
      if (p < 1) anim.current = requestAnimationFrame(schritt);
    };
    anim.current = requestAnimationFrame(schritt);
  }

  useEffect(() => () => void (anim.current && cancelAnimationFrame(anim.current)), []);

  const s = SAISON[saison];
  const kurve = pfad(werte);
  const flaeche = `${kurve} L ${x(24)} ${y(CT_MIN)} L ${x(0)} ${y(CT_MIN)} Z`;

  return (
    <div>
      {/* Saison-Umschalter */}
      <div
        role="radiogroup"
        aria-label="Jahreszeit wählen"
        className="inline-flex rounded-full border border-line bg-mist p-1"
      >
        {(["sommer", "winter"] as const).map((k) => (
          <button
            key={k}
            role="radio"
            aria-checked={saison === k}
            tabIndex={saison === k ? 0 : -1}
            onClick={() => wechseln(k)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                wechseln(k === "sommer" ? "winter" : "sommer");
              }
            }}
            className={`touch-manipulation rounded-full px-5 py-2 text-sm font-bold transition-colors ${
              saison === k ? "bg-volt text-white" : "text-ink-soft hover:text-ink"
            }`}
          >
            {SAISON[k].name}
          </button>
        ))}
      </div>
      <p className="mt-3 text-sm text-ink-soft">{s.hinweis}</p>

      <figure className="mt-6">
        <svg
          viewBox={`0 0 ${B} ${H}`}
          className="w-full"
          role="img"
          aria-label={`Börsenstrompreis im Tagesverlauf, ${s.name}: Tiefstwert ${s.tief.ct} Cent um ${s.tief.stunde} Uhr, Höchstwert ${s.hoch.ct} Cent um ${s.hoch.stunde} Uhr.`}
        >
          <defs>
            <linearGradient id="unterKurve" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#00A878" stopOpacity="0.22" />
              <stop offset="1" stopColor="#00A878" stopOpacity="0" />
            </linearGradient>
            <clipPath id="chartFlaeche">
              <rect x={x(0)} y={PAD.oben} width={x(24) - x(0)} height={y(CT_MIN) - PAD.oben} />
            </clipPath>
          </defs>

          {/* Waagerechte Hilfslinien */}
          {[5, 10, 15, 20].map((ct) => (
            <g key={ct}>
              <line
                x1={x(0)}
                y1={y(ct)}
                x2={x(24)}
                y2={y(ct)}
                stroke="#E2E8EE"
                strokeWidth="1"
              />
              <text x={x(0) - 10} y={y(ct) + 4} textAnchor="end" className="num" fill="#51667F" fontSize="15">
                {ct}
              </text>
            </g>
          ))}

          {/* Das wandernde Tal — beim Umschalten springt es quer über den Chart */}
          <rect
            x={x(s.tal.von)}
            y={PAD.oben}
            width={x(s.tal.bis) - x(s.tal.von)}
            height={y(CT_MIN) - PAD.oben}
            rx="10"
            fill="#00A878"
            opacity="0.1"
            style={{ transition: "x 480ms ease-out, width 480ms ease-out" }}
          />
          <text
            x={(x(s.tal.von) + x(s.tal.bis)) / 2}
            y={PAD.oben - 14}
            textAnchor="middle"
            fill="#00A878"
            fontSize="15"
            fontWeight="700"
            style={{ transition: "x 480ms ease-out" }}
          >
            hier lädt VoltSurfer
          </text>

          {/* Die Abendspitze bleibt, wo sie ist — ganzjährig */}
          <rect
            x={x(ABENDSPITZE.von)}
            y={PAD.oben}
            width={x(ABENDSPITZE.bis) - x(ABENDSPITZE.von)}
            height={y(CT_MIN) - PAD.oben}
            rx="10"
            fill="#C43C3C"
            opacity="0.08"
          />
          <text
            x={(x(ABENDSPITZE.von) + x(ABENDSPITZE.bis)) / 2}
            y={PAD.oben - 14}
            textAnchor="middle"
            fill="#C43C3C"
            fontSize="15"
            fontWeight="700"
          >
            Abendspitze
          </text>

          {/* Jahresmittel als ruhiger Anker */}
          <path
            d={pfad(PROFIL_JAHR)}
            fill="none"
            stroke="#51667F"
            strokeWidth="1.5"
            strokeDasharray="5 5"
            opacity="0.4"
            clipPath="url(#chartFlaeche)"
          />

          {/* Negativzone: unter null bekommst du Geld — also grün, nicht rot */}
          <rect
            x={x(0)}
            y={y(0)}
            width={x(24) - x(0)}
            height={y(CT_MIN) - y(0)}
            fill="#00A878"
            opacity="0.12"
          />
          <line x1={x(0)} y1={y(0)} x2={x(24)} y2={y(0)} stroke="#0B1D33" strokeWidth="1.5" />
          <text x={x(0) - 10} y={y(0) + 4} textAnchor="end" className="num" fill="#0B1D33" fontSize="15" fontWeight="700">
            0
          </text>
          <text x={x(12)} y={y(CT_MIN) - 8} textAnchor="middle" fill="#00A878" fontSize="14" fontWeight="700">
            hier unten liegen 6 % aller Viertelstunden — dann gibt es Geld fürs Laden
          </text>

          {/* Die Tageskurve */}
          <path d={flaeche} fill="url(#unterKurve)" clipPath="url(#chartFlaeche)" />
          <path
            d={kurve}
            fill="none"
            stroke="#00A878"
            strokeWidth="3.5"
            strokeLinecap="round"
            clipPath="url(#chartFlaeche)"
          />

          {/* Tief- und Hochpunkt beschriften */}
          <circle cx={x(s.tief.stunde + 0.5)} cy={y(werte[s.tief.stunde])} r="7" fill="#00A878" />
          <text
            x={x(s.tief.stunde + 0.5)}
            y={y(werte[s.tief.stunde]) + 26}
            textAnchor="middle"
            className="num"
            fill="#00A878"
            fontSize="17"
            fontWeight="700"
          >
            {s.tief.stunde} Uhr · {s.tief.ct.toString().replace(".", ",")} ct
          </text>

          <circle cx={x(s.hoch.stunde + 0.5)} cy={y(werte[s.hoch.stunde])} r="7" fill="#C43C3C" />
          <text
            x={x(s.hoch.stunde + 0.5)}
            y={y(werte[s.hoch.stunde]) - 14}
            textAnchor="middle"
            className="num"
            fill="#C43C3C"
            fontSize="17"
            fontWeight="700"
          >
            {s.hoch.stunde} Uhr · {s.hoch.ct.toString().replace(".", ",")} ct
          </text>

          {/* Stundenachse */}
          {[0, 6, 12, 18, 24].map((h) => (
            <text
              key={h}
              x={x(h)}
              y={H - 18}
              textAnchor={h === 0 ? "start" : h === 24 ? "end" : "middle"}
              className="num"
              fill="#51667F"
              fontSize="15"
            >
              {h} Uhr
            </text>
          ))}
          <text x={x(0) - 10} y={PAD.oben - 12} textAnchor="end" fill="#51667F" fontSize="14">
            ct/kWh
          </text>
        </svg>

        <figcaption className="mt-4 text-sm leading-relaxed text-ink-soft">
          Zwischen der günstigsten und der teuersten Stunde liegt an diesem Tag der{" "}
          <strong className="text-ink">{s.faktor} Preis</strong>. Gestrichelt: der
          Jahresdurchschnitt aller Tage. Börsenpreise ohne Netzentgelte, Umlagen und Steuern.
        </figcaption>
      </figure>

      {/* Für Screenreader: die Kurve als Tabelle */}
      <table className="sr-only">
        <caption>Ø Börsenstrompreis je Stunde, {s.name}, in ct/kWh</caption>
        <tbody>
          {s.profil.map((ct, h) => (
            <tr key={h}>
              <th scope="row">{h} Uhr</th>
              <td>{ct.toString().replace(".", ",")} ct/kWh</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
