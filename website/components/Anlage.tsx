"use client";

import { useEffect, useState } from "react";

/**
 * Die Anlage: das Rendering, über dessen Leitungen animierter Strom fließt.
 *
 * `leitungen.png` ist eine Maske, die exakt die Leitungswege freigibt. Alles,
 * was durch sie gezeichnet wird, erscheint nur dort — so wandern Lichtstreifen
 * über die Leitungen, ohne dass das Bild selbst verändert wird.
 *
 * Zwei Tageszeiten lösen sich ab: mittags lädt der Speicher aus dem Netz,
 * abends versorgt er Haus, Wärmepumpe und Auto.
 */

type Phase = "laden" | "versorgen";

const PHASEN: Record<Phase, { zeit: string; text: string; farbe: string }> = {
  laden: { zeit: "13:15", text: "Strom kostet 2 Cent — der Speicher lädt", farbe: "var(--color-cyan)" },
  versorgen: { zeit: "19:30", text: "Strom kostet 18 Cent — das Haus lebt vom Speicher", farbe: "var(--color-bernstein)" },
};

/** Punkte im Bild (1024er-Raster), an denen Energie ankommt. */
const LEUCHTEN = [
  { x: 332, y: 572, r: 60, phase: "versorgen" as Phase },
  { x: 540, y: 578, r: 74, phase: "laden" as Phase },
  { x: 588, y: 578, r: 50, phase: "versorgen" as Phase },
  { x: 893, y: 640, r: 62, phase: "laden" as Phase },
];

const maske: React.CSSProperties = {
  WebkitMaskImage: "url(/anlage/leitungen.png)",
  maskImage: "url(/anlage/leitungen.png)",
  WebkitMaskSize: "100% 100%",
  maskSize: "100% 100%",
  WebkitMaskRepeat: "no-repeat",
  maskRepeat: "no-repeat",
};

export function Anlage() {
  const [phase, setPhase] = useState<Phase>("laden");
  const [ruhig, setRuhig] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setRuhig(true);
      return;
    }
    const t = setInterval(() => setPhase((p) => (p === "laden" ? "versorgen" : "laden")), 5000);
    return () => clearInterval(t);
  }, []);

  const p = PHASEN[phase];

  return (
    <div className="relative">
      {/* Haus und Bildhintergrund sind dieselbe Blaufamilie — freistellen würde
          das Dach anfressen. Stattdessen läuft das Bild an den Rändern weich
          aus, sodass kein Kasten sichtbar bleibt. Der Seitenhintergrund
          dahinter trägt denselben Ton wie das Rendering. */}
      <div
        className="relative aspect-[7/5] w-full overflow-hidden"
        style={{
          maskImage:
            "radial-gradient(128% 116% at 50% 50%, #000 42%, rgba(0,0,0,0.9) 62%, rgba(0,0,0,0.45) 80%, transparent 96%)",
          WebkitMaskImage:
            "radial-gradient(128% 116% at 50% 50%, #000 42%, rgba(0,0,0,0.9) 62%, rgba(0,0,0,0.45) 80%, transparent 96%)",
        }}
      >
        <div className="absolute left-1/2 top-1/2 aspect-square w-[132%] -translate-x-1/2 -translate-y-1/2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/anlage/haus.png"
            alt="Wohnhaus mit Batteriespeicher, Wärmepumpe, Wallbox und Carport mit Elektroauto, verbunden mit dem Stromnetz"
            className="absolute inset-0 size-full object-contain"
          />

          {/* Wandernde Lichtstreifen, nur auf den Leitungen sichtbar */}
          {[-27, 27].map((winkel, i) => (
            <div
              key={winkel}
              className="pointer-events-none absolute inset-0 overflow-hidden"
              style={{ ...maske, mixBlendMode: "screen" }}
              aria-hidden="true"
            >
              <div
                className={ruhig ? "" : "stromfluss"}
                style={{
                  position: "absolute",
                  inset: "-100%",
                  ["--winkel" as string]: `${winkel}deg`,
                  transform: `rotate(${winkel}deg)`,
                  animationDelay: `${i * -1.4}s`,
                  backgroundImage: `repeating-linear-gradient(90deg,
                    rgba(255,255,255,0) 0px, rgba(255,255,255,0) 120px,
                    rgba(190,255,215,0.5) 150px, rgba(255,255,255,0.95) 162px,
                    rgba(190,255,215,0.5) 174px,
                    rgba(255,255,255,0) 206px, rgba(255,255,255,0) 240px)`,
                }}
              />
            </div>
          ))}

          {/* Leuchten an den Geräten, je nach Tageszeit */}
          {LEUCHTEN.map((l) => (
            <div
              key={`${l.x}-${l.y}`}
              className="pointer-events-none absolute rounded-full transition-opacity duration-1000"
              style={{
                left: `${((l.x - l.r) / 1024) * 100}%`,
                top: `${((l.y - l.r) / 1024) * 100}%`,
                width: `${((l.r * 2) / 1024) * 100}%`,
                height: `${((l.r * 2) / 1024) * 100}%`,
                mixBlendMode: "screen",
                opacity: l.phase === phase ? 0.8 : 0.1,
                background:
                  "radial-gradient(circle, rgba(126,255,170,0.55) 0%, rgba(126,255,170,0.16) 45%, transparent 70%)",
              }}
              aria-hidden="true"
            />
          ))}
        </div>
      </div>

      {/* Was gerade passiert */}
      <div
        className="mt-1 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center"
        aria-live="polite"
      >
        <span className="zahl font-semibold" style={{ color: p.farbe }}>
          {p.zeit} Uhr
        </span>
        <span className="text-text-leise">{p.text}</span>
      </div>
    </div>
  );
}
