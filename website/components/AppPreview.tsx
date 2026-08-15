import { Lock } from "lucide-react";

import { ECKZAHLEN, PROFIL_SOMMER } from "@/lib/preise";

/**
 * Glasige Vorschau der VoltSurfer-Oberfläche mit Beispielwerten eines
 * Sommertags. Die Mini-Kurve zeigt dieselben Stundenwerte wie der große Chart.
 */
export function AppPreview({ className = "" }: { className?: string }) {
  const umfang = 2 * Math.PI * 56;
  const soc = 0.82;

  // Mini-Kurve: dieselben 24 Werte, gestaucht auf 240 × 46
  const punkte = PROFIL_SOMMER.map((ct, h) => {
    const x = 8 + (h / 23) * 240;
    const y = 50 - ((ct - 0) / 19) * 40;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  return (
    <div
      className={`glass w-[340px] rounded-3xl p-6 shadow-[0_0_80px_rgba(0,229,160,0.1)] ${className}`}
      aria-label="Vorschau der VoltSurfer-App mit Beispielwerten"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-white/80">Deine Anlage</p>
        <p className="font-mono text-[11px] font-semibold tracking-wider text-white/45">
          BEISPIELANSICHT
        </p>
      </div>

      {/* Ladestand */}
      <div className="relative mx-auto mt-5 size-40">
        <svg viewBox="0 0 128 128" className="size-full -rotate-90">
          <defs>
            <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#00E5A0" />
              <stop offset="1" stopColor="#38BDF8" />
            </linearGradient>
          </defs>
          <circle cx="64" cy="64" r="56" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
          <circle
            cx="64"
            cy="64"
            r="56"
            fill="none"
            stroke="url(#ring)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={umfang}
            strokeDashoffset={umfang * (1 - soc)}
            style={{ filter: "drop-shadow(0 0 6px rgba(0,229,160,0.55))" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-content-center text-center">
          <p className="num font-mono text-3xl font-semibold text-white">82&thinsp;%</p>
          <p className="num text-xs text-white/55">24,6 von 30 kWh</p>
        </div>
      </div>

      {/* Tageszahlen */}
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
          <p className="text-xs text-white/55">Heute geladen</p>
          <p className="num mt-1 font-mono text-lg font-semibold text-white">
            21,4 <span className="text-sm font-medium text-white/55">kWh</span>
          </p>
          <p className="num font-mono text-xs text-volt-bright">
            Ø {ECKZAHLEN.einkaufspreis.toString().replace(".", ",")} ct
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
          <p className="text-xs text-white/55">Haus versorgt</p>
          <p className="num mt-1 font-mono text-lg font-semibold text-volt-bright">+2,25 €</p>
          <p className="text-xs text-white/55">statt Netzbezug</p>
        </div>
      </div>

      {/* Verkauf — als Zukunft gekennzeichnet */}
      <div className="mt-3 flex items-center justify-between rounded-2xl border border-sun/25 bg-sun/10 px-4 py-3">
        <div>
          <p className="flex items-center gap-1.5 text-xs text-white/60">
            <Lock className="size-3" aria-hidden="true" />
            Ins Netz verkauft
          </p>
          <p className="num mt-1 font-mono text-lg font-semibold text-white">
            4,8 <span className="text-sm font-medium text-white/55">kWh</span>
          </p>
        </div>
        <p className="max-w-[9rem] text-right text-[11px] leading-tight text-white/50">
          sobald der Verbund steht
        </p>
      </div>

      {/* Preiskurve morgen */}
      <div className="mt-3 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
        <div className="flex items-baseline justify-between">
          <p className="text-xs text-white/55">Börsenpreis morgen</p>
          <p className="font-mono text-xs text-white/45">ct/kWh</p>
        </div>
        <svg viewBox="0 0 256 60" className="mt-2 w-full" aria-hidden="true">
          <rect x="106" y="4" width="60" height="46" rx="6" fill="#00E5A0" opacity="0.16" />
          <rect x="196" y="4" width="44" height="46" rx="6" fill="#C43C3C" opacity="0.14" />
          <polyline points={punkte} fill="none" stroke="#00E5A0" strokeWidth="2" strokeLinejoin="round" />
          <text x="136" y="58" textAnchor="middle" fill="#00E5A0" fontSize="9" fontFamily="var(--font-plex)">
            laden
          </text>
          <text x="218" y="58" textAnchor="middle" fill="#E88" fontSize="9" fontFamily="var(--font-plex)">
            entladen
          </text>
        </svg>
      </div>

      <p className="num mt-4 flex items-center justify-between rounded-full border border-volt-bright/25 bg-volt-bright/10 px-4 py-2.5 text-xs font-semibold text-white">
        Nächstes Ladefenster
        <span className="font-mono text-volt-bright">11:45–14:15 · 2,1 ct</span>
      </p>
    </div>
  );
}
