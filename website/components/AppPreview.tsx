/**
 * Glasige App-Karte im Stil moderner Smart-Home-Dashboards: Ladestand-Ring,
 * Tageszahlen und Mini-Preiskurve. Zeigt Beispielwerte aus der Simulation —
 * dieselben Größen, die die echte VoltSurfer-Oberfläche anzeigt.
 */
export function AppPreview({ className = "" }: { className?: string }) {
  // Ring: r=56 → Umfang ≈ 352; 82 % Ladestand
  const umfang = 2 * Math.PI * 56;
  const soc = 0.82;

  return (
    <div
      className={`w-[340px] rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-[0_0_80px_rgba(0,229,160,0.12),inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md ${className}`}
      aria-label="Vorschau der VoltSurfer-App mit Beispielwerten"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-white/80">Deine Anlage</p>
        <p className="flex items-center gap-1.5 font-mono text-xs font-semibold text-volt-bright">
          <span className="relative flex size-2" aria-hidden="true">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-volt-bright opacity-60 motion-reduce:animate-none" />
            <span className="relative inline-flex size-2 rounded-full bg-volt-bright" />
          </span>
          LIVE
        </p>
      </div>

      {/* Ladestand-Ring */}
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
          <p className="font-mono text-3xl font-semibold text-white">82&thinsp;%</p>
          <p className="text-xs text-white/55">24,6 von 30 kWh</p>
        </div>
      </div>

      {/* Tageszahlen */}
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3">
          <p className="text-xs text-white/55">Heute geladen</p>
          <p className="mt-1 font-mono text-lg font-semibold text-white">
            21,4 <span className="text-sm font-medium text-white/55">kWh</span>
          </p>
          <p className="font-mono text-xs text-volt-bright">Ø 6,8 ct</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3">
          <p className="text-xs text-white/55">Tagesbilanz</p>
          <p className="mt-1 font-mono text-lg font-semibold text-volt-bright">+3,69 €</p>
          <p className="font-mono text-xs text-white/55">vs. Netzbezug</p>
        </div>
      </div>

      {/* Mini-Preiskurve mit Ladefenstern */}
      <div className="mt-3 rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3">
        <div className="flex items-baseline justify-between">
          <p className="text-xs text-white/55">Börsenpreis morgen</p>
          <p className="font-mono text-xs text-white/55">ct/kWh</p>
        </div>
        <svg viewBox="0 0 272 64" className="mt-2 w-full" aria-hidden="true">
          <rect x="10" y="6" width="52" height="46" rx="6" fill="#00E5A0" opacity="0.14" />
          <rect x="122" y="6" width="40" height="46" rx="6" fill="#00E5A0" opacity="0.14" />
          <rect x="192" y="6" width="46" height="46" rx="6" fill="#E05252" opacity="0.14" />
          <path
            d="M4 40 C 30 46, 48 44, 62 36 S 96 14, 116 18 S 148 40, 164 42 S 196 30, 214 12 S 248 10, 268 24"
            fill="none"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.5"
          />
          <path
            d="M4 40 C 30 46, 48 44, 62 36 S 96 14, 116 18 S 148 40, 164 42 S 196 30, 214 12 S 248 10, 268 24"
            fill="none"
            stroke="#00E5A0"
            strokeWidth="2"
            strokeLinecap="round"
            className="animate-flow"
          />
          <circle cx="36" cy="43" r="4" fill="#00E5A0" style={{ filter: "drop-shadow(0 0 4px #00E5A0)" }} />
          <circle cx="215" cy="12" r="4" fill="#E05252" style={{ filter: "drop-shadow(0 0 4px #E05252)" }} />
          <text x="36" y="62" textAnchor="middle" fill="#00E5A0" fontSize="9" fontFamily="var(--font-plex)">
            laden
          </text>
          <text x="215" y="62" textAnchor="middle" fill="#E05252" fontSize="9" fontFamily="var(--font-plex)">
            entladen
          </text>
        </svg>
      </div>

      {/* Nächstes Fenster */}
      <p className="mt-4 flex items-center justify-between rounded-full border border-volt-bright/25 bg-volt-bright/10 px-4 py-2.5 text-xs font-semibold text-white">
        Nächstes Ladefenster
        <span className="font-mono text-volt-bright">01:45–04:15 · 7,9 ct</span>
      </p>
    </div>
  );
}
