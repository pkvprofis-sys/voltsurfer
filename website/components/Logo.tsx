export function Logo({ className = "", dark = false }: { className?: string; dark?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-2 font-display font-extrabold tracking-tight ${
        dark ? "text-white" : "text-ink"
      } ${className}`}
      translate="no"
    >
      <svg viewBox="0 0 32 32" className="size-7 shrink-0" aria-hidden="true">
        <rect width="32" height="32" rx="9" fill={dark ? "#00E5A0" : "#0B1D33"} />
        <path
          d="M6 21 Q12 10 16 16 T26 12"
          stroke={dark ? "#0B1D33" : "#00E5A0"}
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
        />
        <path d="M17 6 L12 17h4l-2 9 7-12h-4z" fill={dark ? "#0B1D33" : "#00E5A0"} />
      </svg>
      VoltSurfer
    </span>
  );
}
