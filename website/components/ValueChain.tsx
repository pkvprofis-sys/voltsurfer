import { BatteryCharging, House, Lock, TrendingUp } from "lucide-react";

import { BLOCK_MITTEL, ECKZAHLEN, ERSPARNIS } from "@/lib/preise";

/**
 * Die Verwertungskette in drei Stufen. Entscheidend ist die visuelle Trennung
 * der Zeitebenen: Grün und durchgezogen = läuft ab Installation. Bernstein und
 * gestrichelt = kommt mit dem Verbund. Dieselbe Kennzeichnung wie in der App
 * (✅ heute / 🔓 Vermarktung).
 */
const STUFEN = [
  {
    icon: BatteryCharging,
    titel: "Einkaufen",
    text: "In den günstigsten Viertelstunden des Tages lädt der Speicher mit 11 kW — wann die liegen, entscheidet die Steuerung jeden Tag neu.",
    wert: `Ø ${ECKZAHLEN.einkaufspreis.toString().replace(".", ",")} ct/kWh`,
    wertText: "Preis der zwei günstigsten Stunden",
    zukunft: false,
  },
  {
    icon: House,
    titel: "Selbst verbrauchen",
    text: "Haushalt und Wärmepumpe laufen aus dem Speicher, während das Netz den Abendpreis verlangt. Du merkst davon nichts außer an der Rechnung.",
    wert: `statt ${BLOCK_MITTEL.abend.ct.toString().replace(".", ",")} ct/kWh`,
    wertText: "Ø Börsenpreis in der Abendspitze",
    zukunft: false,
  },
  {
    icon: TrendingUp,
    titel: "Ins Netz verkaufen",
    text: "Was über deinem Bedarf im Speicher liegt, geht zu Höchstpreisen zurück ins Netz — gebündelt mit allen anderen VoltSurfer-Anlagen.",
    wert: "Erlös = Börsenpreis",
    wertText: "über den VoltSurfer-Verbund",
    zukunft: true,
  },
];

export function ValueChain() {
  return (
    <section id="kette" className="scroll-mt-24 py-20 lg:py-32">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
          Dein Bedarf ist reserviert. Gehandelt wird mit dem, was darüber hinaus reinpasst.
        </h2>
        <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-ink-soft text-pretty">
          Der Speicher lädt in den günstigen Stunden nicht nur für dich — er füllt bewusst
          weiter auf, um am Abend zum Höchstpreis ins Netz zu geben. Ein Puffer für deinen
          eigenen Verbrauch bleibt dabei immer gesperrt.
        </p>

        <ol className="mt-12 grid gap-6 md:grid-cols-3 lg:mt-16">
          {STUFEN.map((s, i) => (
            <li
              key={s.titel}
              className={`rounded-3xl p-7 ${
                s.zukunft
                  ? "border-2 border-dashed border-sun/50 bg-sun-wash"
                  : "border border-line bg-paper"
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`grid size-11 place-items-center rounded-2xl ${
                    s.zukunft ? "bg-sun text-white" : "bg-volt text-white"
                  }`}
                >
                  <s.icon className="size-5" aria-hidden="true" />
                </span>
                <span className="num font-mono text-sm font-semibold text-ink-soft">
                  Schritt {i + 1}
                </span>
              </div>

              <h3 className="mt-5 font-display text-xl font-bold">{s.titel}</h3>
              <p className="mt-2 leading-relaxed text-ink-soft text-pretty">{s.text}</p>

              <p className="num mt-5 font-mono text-lg font-semibold text-ink">{s.wert}</p>
              <p className="text-sm text-ink-soft">{s.wertText}</p>

              <p
                className={`mt-5 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-bold ${
                  s.zukunft ? "bg-sun/15 text-sun" : "bg-volt-wash text-volt"
                }`}
              >
                {s.zukunft ? (
                  <>
                    <Lock className="size-3.5" aria-hidden="true" />
                    sobald der Verbund steht
                  </>
                ) : (
                  <>✓ heute schon aktiv</>
                )}
              </p>
            </li>
          ))}
        </ol>

        {/* Woher die Ersparnis kommt */}
        <div className="mt-14 rounded-3xl border border-line bg-mist p-7 sm:p-9">
          <h3 className="font-display text-xl font-bold">
            Woher die {ERSPARNIS.gesamt.toLocaleString("de-DE")} € kommen
          </h3>

          <div className="mt-6 flex h-14 overflow-hidden rounded-2xl" aria-hidden="true">
            <div
              className="grid place-items-center bg-volt text-sm font-bold text-white"
              style={{ width: `${ERSPARNIS.anteilHeute}%` }}
            >
              {ERSPARNIS.anteilHeute} %
            </div>
            <div
              className="grid place-items-center border-l-2 border-paper text-sm font-bold text-sun"
              style={{
                width: `${ERSPARNIS.anteilVerbund}%`,
                background:
                  "repeating-linear-gradient(45deg, #FDF3E2, #FDF3E2 7px, #F7E3C0 7px, #F7E3C0 14px)",
              }}
            >
              {ERSPARNIS.anteilVerbund} %
            </div>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <p className="flex gap-3 text-sm leading-relaxed text-ink-soft">
              <span className="mt-1 size-3 shrink-0 rounded-sm bg-volt" aria-hidden="true" />
              <span>
                <strong className="text-ink">
                  Rund {ERSPARNIS.heute} € ab dem Tag der Installation
                </strong>{" "}
                — günstig laden, Haus versorgen, reduziertes Netzentgelt nach § 14a.
              </span>
            </p>
            <p className="flex gap-3 text-sm leading-relaxed text-ink-soft">
              <span
                className="mt-1 size-3 shrink-0 rounded-sm border border-sun/40"
                style={{
                  background:
                    "repeating-linear-gradient(45deg, #FDF3E2, #FDF3E2 3px, #F7E3C0 3px, #F7E3C0 6px)",
                }}
                aria-hidden="true"
              />
              <span>
                <strong className="text-ink">Der Rest kommt aus der Vermarktung</strong> über
                den Verbund. Er halbiert die Amortisationszeit von rund{" "}
                {ERSPARNIS.amortisation.ohneVerbund} auf {ERSPARNIS.amortisation.mitVerbund}{" "}
                Jahre.
              </span>
            </p>
          </div>
        </div>

        {/* Frühkunden */}
        <div className="mt-6 rounded-3xl border-2 border-sun/40 bg-sun-wash p-7 sm:p-9">
          <h3 className="font-display text-xl font-bold">Du bist von Anfang an dabei.</h3>
          <p className="mt-3 max-w-[65ch] leading-relaxed text-ink-soft text-pretty">
            Der Verbund startet, sobald rund 20 bis 30 Haushalte zusammengeschaltet sind.
            Wer jetzt einsteigt, ist von der ersten Handelsstunde an dabei — ohne
            Nachrüstung, ohne neues Gerät, ohne Aufpreis. Bis dahin verdient dein Speicher
            schon mit dem, was heute geht.
          </p>
        </div>
      </div>
    </section>
  );
}
