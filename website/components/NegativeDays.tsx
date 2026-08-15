import { NEGATIV, NEGATIV_MONATE, NEGATIV_TAGE, ZEITRAUM } from "@/lib/preise";

/**
 * Ein Balken je Tag der letzten 12 Monate. Leuchtet, wenn der Börsenpreis an
 * diesem Tag mindestens eine Viertelstunde lang negativ war. Das Frühjahrs- und
 * Sommercluster sieht man sofort — ohne einen Satz Erklärung.
 */
function Streifen() {
  const tage = NEGATIV_TAGE.split("");
  return (
    <div className="animate-wipe mt-10">
      <div className="flex h-24 items-stretch gap-px" aria-hidden="true">
        {tage.map((t, i) => (
          <div
            key={i}
            className={`flex-1 rounded-[1px] ${
              t === "1" ? "bg-volt-bright" : "bg-white/[0.08]"
            }`}
            style={t === "1" ? { boxShadow: "0 0 6px rgba(0,229,160,0.5)" } : undefined}
          />
        ))}
      </div>
      <div className="mt-3 flex justify-between font-mono text-[11px] text-white/45">
        {NEGATIV_MONATE.map((m, i) => (
          <span key={i}>{m.label}</span>
        ))}
      </div>
      <p className="sr-only">
        An {NEGATIV.tageAbsolut} von {NEGATIV.tageGesamt} Tagen im Zeitraum {ZEITRAUM} war
        der Börsenstrompreis mindestens eine Viertelstunde lang negativ. Die meisten
        dieser Tage liegen zwischen März und August.
      </p>
    </div>
  );
}

export function NegativeDays() {
  const karten = [
    {
      wert: `${NEGATIV.anteilTage} %`,
      text: "der Tage haben mindestens eine Viertelstunde mit negativem Preis",
    },
    {
      wert: `${NEGATIV.dauerStunden.toString().replace(".", ",")} Std.`,
      text: "hält der negative Preis an solchen Tagen im Schnitt an",
    },
    {
      wert: `${NEGATIV.trend[0].anteil.toString().replace(".", ",")} % → ${NEGATIV.trend[3].anteil
        .toString()
        .replace(".", ",")} %`,
      text: "Anteil negativer Viertelstunden 2023 gegenüber 2026 — es wird mehr, nicht weniger",
    },
  ];

  return (
    <section className="bg-night py-20 text-white lg:py-32">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
          An jedem vierten Tag kostet Strom zeitweise weniger als nichts.
        </h2>
        <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-white/70 text-pretty">
          Wenn Wind und Sonne mehr liefern, als gebraucht wird, rutscht der Börsenpreis
          ins Minus — dann bekommt Geld, wer Strom abnimmt. Das ist keine Kuriosität mehr,
          sondern ein Muster: Im April 2026 war der{" "}
          <strong className="text-white">durchschnittliche</strong> Mittagspreis über den
          ganzen Monat negativ.
        </p>

        <Streifen />

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {karten.map((k) => (
            <div key={k.text} className="glass rounded-3xl p-7">
              <p className="num font-mono text-3xl font-semibold text-volt-bright">{k.wert}</p>
              <p className="mt-3 leading-relaxed text-white/70 text-pretty">{k.text}</p>
            </div>
          ))}
        </div>

        <p className="mt-10 max-w-[65ch] text-lg leading-relaxed text-white/80 text-pretty">
          Für dich heißt das: In diesen Stunden lädt dein Speicher nicht nur umsonst —
          er verdient schon beim Laden.
        </p>
      </div>
    </section>
  );
}
