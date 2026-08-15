/**
 * Der Strompreis über einen Tag: günstige Fenster (nachts, mittags) und die
 * teure Abendspitze. Zeigt anschaulich, wovon VoltSurfer lebt.
 */
export function PriceWave({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 480 220"
      className={className}
      role="img"
      aria-label="Tagesverlauf des Börsenstrompreises: nachts und mittags günstig, abends teuer"
    >
      <defs>
        <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0284C7" stopOpacity="0.18" />
          <stop offset="1" stopColor="#0284C7" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Günstige Fenster */}
      <rect x="16" y="24" width="92" height="140" rx="12" fill="#00E5A0" opacity="0.16" />
      <rect x="214" y="24" width="74" height="140" rx="12" fill="#00E5A0" opacity="0.16" />
      {/* Teure Abendspitze */}
      <rect x="330" y="24" width="80" height="140" rx="12" fill="#E05252" opacity="0.12" />

      <path
        d="M16 138 C 64 144, 84 142, 104 128 S 156 58, 196 64 S 240 128, 266 132 S 306 114, 336 72 S 376 40, 412 58 S 452 96, 464 104"
        fill="none"
        stroke="#0284C7"
        strokeWidth="3.5"
        strokeLinecap="round"
      />
      <path
        d="M16 138 C 64 144, 84 142, 104 128 S 156 58, 196 64 S 240 128, 266 132 S 306 114, 336 72 S 376 40, 412 58 S 452 96, 464 104 L 464 168 L 16 168 Z"
        fill="url(#fill)"
      />
      <path
        d="M16 138 C 64 144, 84 142, 104 128 S 156 58, 196 64 S 240 128, 266 132 S 306 114, 336 72 S 376 40, 412 58 S 452 96, 464 104"
        fill="none"
        stroke="#00A878"
        strokeWidth="3.5"
        strokeLinecap="round"
        className="animate-flow"
      />

      <circle cx="62" cy="141" r="8" fill="#00A878" />
      <circle cx="251" cy="131" r="8" fill="#00A878" />
      <circle cx="374" cy="47" r="8" fill="#E05252" />

      <text x="62" y="192" textAnchor="middle" fill="#00A878" fontSize="14" fontWeight="700">
        laden
      </text>
      <text x="251" y="192" textAnchor="middle" fill="#00A878" fontSize="14" fontWeight="700">
        laden
      </text>
      <text x="372" y="192" textAnchor="middle" fill="#E05252" fontSize="14" fontWeight="700">
        nutzen
      </text>

      <text x="16" y="212" fill="#4D6280" fontSize="12">
        0 Uhr
      </text>
      <text x="240" y="212" textAnchor="middle" fill="#4D6280" fontSize="12">
        12 Uhr
      </text>
      <text x="464" y="212" textAnchor="end" fill="#4D6280" fontSize="12">
        24 Uhr
      </text>
    </svg>
  );
}
