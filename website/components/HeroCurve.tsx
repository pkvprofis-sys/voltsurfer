import { PROFIL_SOMMER } from "@/lib/preise";

const B = 1200;
const H = 420;

/** Weiche Kurve durch die 24 Stundenwerte, über die volle Hero-Breite gezogen. */
function pfad() {
  const min = -1;
  const max = 20;
  const p = PROFIL_SOMMER.map((ct, h) => {
    const x = (h / 23) * B;
    const y = H - ((ct - min) / (max - min)) * (H * 0.62) - H * 0.12;
    return [x, y] as const;
  });
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

/**
 * Der Hero-Hintergrund ist die echte Tageskurve eines Sommertags — tief am
 * Mittag, steil am Abend. Der Leuchtpunkt surft sie entlang: die Marke,
 * wörtlich genommen.
 */
export function HeroCurve({ className = "" }: { className?: string }) {
  const d = pfad();
  return (
    <svg
      viewBox={`0 0 ${B} ${H}`}
      preserveAspectRatio="none"
      aria-hidden="true"
      className={`pointer-events-none absolute inset-x-0 bottom-0 h-[62%] w-full ${className}`}
    >
      <defs>
        <linearGradient id="heroFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#00E5A0" stopOpacity="0.16" />
          <stop offset="1" stopColor="#00E5A0" stopOpacity="0" />
        </linearGradient>
        <filter id="heroGlow" x="-20%" y="-60%" width="140%" height="260%">
          <feGaussianBlur stdDeviation="14" />
        </filter>
      </defs>

      <path d={`${d} L ${B} ${H} L 0 ${H} Z`} fill="url(#heroFill)" />
      <path d={d} fill="none" stroke="#00E5A0" strokeWidth="6" opacity="0.5" filter="url(#heroGlow)" />
      <path d={d} fill="none" stroke="#00E5A0" strokeWidth="2.5" strokeLinecap="round" />

      <circle r="7" fill="#ffffff" className="animate-surf" style={{ offsetPath: `path("${d}")` }} />
      <circle
        r="16"
        fill="#00E5A0"
        opacity="0.35"
        filter="url(#heroGlow)"
        className="animate-surf"
        style={{ offsetPath: `path("${d}")` }}
      />
    </svg>
  );
}
