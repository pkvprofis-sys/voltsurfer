import { PiggyBank, Sparkles, Unlock } from "lucide-react";

import { AppPreview } from "@/components/AppPreview";
import { ContactForm } from "@/components/ContactForm";
import { Faq } from "@/components/Faq";
import { HeroCurve } from "@/components/HeroCurve";
import { Logo } from "@/components/Logo";
import { NegativeDays } from "@/components/NegativeDays";
import { PriceDay } from "@/components/PriceDay";
import { ValueChain } from "@/components/ValueChain";
import { BLOCK_MITTEL, ECKZAHLEN, ENDKUNDE, ERSPARNIS, NEGATIV, ZEITRAUM } from "@/lib/preise";

const DEMO_URL = process.env.NEXT_PUBLIC_DEMO_URL;

const EINWAENDE = [
  {
    frage: "Geht das auf die Batterie?",
    antwort:
      "Wir rechnen den Verschleiß mit ein. Ein Ladezyklus wird nur gefahren, wenn er sich nach Abzug der Batteriealterung lohnt. Die LFP-Zellen halten 6.000 Zyklen.",
  },
  {
    frage: "Muss ich mich darum kümmern?",
    antwort:
      "Nein. Die Steuerung plant jede Nacht neu, mit den Börsenpreisen für morgen und der Wettervorhersage. Du kannst zuschauen, wenn du magst — musst aber nichts einstellen.",
  },
  {
    frage: "Und wenn ich schon PV habe?",
    antwort:
      "Dann hat dein Solarstrom immer Vorrang. Der Speicher wird nur so weit aus dem Netz geladen, wie am nächsten Tag Platz bleibt — die Sonnenprognose fließt in die Planung ein.",
  },
  {
    frage: "Und wenn der Verbund nie kommt?",
    antwort:
      `Dann rechnet sich deine Anlage trotzdem — mit den rund ${ERSPARNIS.heute} € im Jahr, die ab Tag eins laufen. Die Vermarktung ist der Aufschlag obendrauf, nicht die Grundlage. Deshalb zeigen wir dir im Angebot beide Rechnungen getrennt.`,
  },
];

export default function Home() {
  return (
    <>
      <header className="sticky top-0 z-50 border-b border-white/10 bg-night/85 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4 lg:px-8">
          <a href="#top" aria-label="VoltSurfer — zur Startseite">
            <Logo className="text-xl" dark />
          </a>
          <div className="flex items-center gap-6">
            <a href="#markt" className="hidden text-sm font-semibold text-white/70 hover:text-white sm:block">
              Preise am Markt
            </a>
            <a href="#kette" className="hidden text-sm font-semibold text-white/70 hover:text-white sm:block">
              So funktioniert&apos;s
            </a>
            <a
              href="#kontakt"
              className="touch-manipulation rounded-full bg-volt-bright px-5 py-2.5 text-sm font-bold text-night transition-opacity hover:opacity-90"
            >
              Beratung anfragen
            </a>
          </div>
        </nav>
      </header>

      <main id="top">
        {/* ---------------------------------------------------------- Hero */}
        <section className="relative overflow-hidden bg-night text-white">
          <HeroCurve />
          {/* Hält die Kurve vom Text fern, ohne sie abzuschneiden */}
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-r from-night via-night/70 to-transparent lg:to-night/10"
            aria-hidden="true"
          />
          <div className="relative mx-auto grid min-h-[80svh] max-w-6xl content-center items-center gap-12 px-6 py-20 lg:grid-cols-[1fr_auto] lg:px-8">
            <div>
              <p className="animate-rise font-mono text-sm font-semibold tracking-widest text-volt-bright">
                AN {ECKZAHLEN.tiefstpreisMittags} % DER TAGE IST STROM MITTAGS AM BILLIGSTEN
                — NICHT NACHTS
              </p>

              <h1 className="animate-rise delay-1 mt-5 max-w-[20ch] font-display text-[clamp(2.6rem,7vw,4.5rem)] font-extrabold leading-[1.02] tracking-tight text-balance">
                Mittags 5&nbsp;Cent.
                <br />
                Abends 14.
                <br />
                <span className="text-volt-bright">Manchmal unter null.</span>
              </h1>

              <p className="animate-rise delay-2 mt-6 max-w-[52ch] text-lg leading-relaxed text-white/75 text-pretty sm:text-xl">
                Die günstigste Stunde wandert — im Sommer fast immer in die Mittagssonne,
                im Winter zurück in die Nacht. Nur der Abend ist ganzjährig teuer.
                VoltSurfer plant jeden Tag neu: kauft in den billigsten Stunden ein und
                versorgt damit dein Haus, wenn alle anderen den Höchstpreis zahlen.
              </p>

              {/* Die Zahl mit dem Hinweis, der dazugehört */}
              <div className="animate-rise delay-3 mt-8 max-w-lg rounded-2xl border border-white/10 border-l-4 border-l-sun bg-night-card/95 py-5 pl-5 pr-6 backdrop-blur">
                <p className="num font-display text-3xl font-extrabold sm:text-4xl">
                  Bis zu {ERSPARNIS.gesamt.toLocaleString("de-DE")} € im Jahr
                </p>
                <p className="mt-2 leading-relaxed text-white/75 text-pretty">
                  Rund {ERSPARNIS.heute} € davon entstehen ab dem Tag der Installation bei
                  dir zu Hause. Der Rest kommt aus der Vermarktung über den
                  VoltSurfer-Verbund — dabei bist du von Anfang an.
                </p>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href="#kontakt"
                  className="touch-manipulation rounded-full bg-volt-bright px-7 py-4 text-lg font-bold text-night transition-opacity hover:opacity-90"
                >
                  Kostenlos beraten lassen
                </a>
                <a
                  href="#demo"
                  className="touch-manipulation rounded-full border-2 border-white/25 px-7 py-4 text-lg font-bold text-white transition-colors hover:border-white/60"
                >
                  Erst mal durchrechnen
                </a>
              </div>

              <dl className="num mt-12 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/10 pt-6 font-mono text-sm text-white/60">
                <div>
                  <dt className="inline">Ø Tagesspanne&nbsp;</dt>
                  <dd className="inline font-semibold text-white">
                    {ECKZAHLEN.tagesspanne.toString().replace(".", ",")} ct/kWh
                  </dd>
                </div>
                <div>
                  <dt className="inline">Viertelstunden im Minus&nbsp;</dt>
                  <dd className="inline font-semibold text-white">
                    {NEGATIV.anteilViertelstunden.toString().replace(".", ",")} %
                  </dd>
                </div>
                <div>
                  <dt className="inline">Laden &amp; Entladen&nbsp;</dt>
                  <dd className="inline font-semibold text-white">11 kW</dd>
                </div>
              </dl>
            </div>

            <AppPreview className="animate-rise delay-2 justify-self-center lg:justify-self-end" />
          </div>
        </section>

        {/* ------------------------------------------------ Vertrauensleiste */}
        <section className="border-b border-line">
          <div className="mx-auto grid max-w-6xl gap-6 px-6 py-8 sm:grid-cols-3 lg:px-8">
            {[
              { icon: PiggyBank, text: "Dein Speicher, gekauft — kein Abo, keine Gebühr" },
              { icon: Sparkles, text: "Plant sich jede Nacht selbst, mit Preisen und Wetter" },
              { icon: Unlock, text: "Offene OpenEMS-Software, keine Herstellerbindung" },
            ].map((v) => (
              <p key={v.text} className="flex items-center gap-3 text-sm font-semibold text-ink-soft">
                <v.icon className="size-5 shrink-0 text-volt" aria-hidden="true" />
                {v.text}
              </p>
            ))}
          </div>
        </section>

        {/* ------------------------------------------------ Der Markt */}
        <section id="markt" className="scroll-mt-24 py-20 lg:py-32">
          <div className="mx-auto max-w-6xl px-6 lg:px-8">
            <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
              Die billigste Stunde wandert.
            </h2>
            <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-ink-soft text-pretty">
              Vor zehn Jahren war Nachtstrom günstig. Heute drückt Solarstrom den Preis
              mittags nach unten — im Sommerhalbjahr an{" "}
              {ECKZAHLEN.tiefstpreisMittagsSommer} % der Tage. Im Winter kehrt es sich um:
              Dann kostet die Kilowattstunde mittags rund 3 Cent{" "}
              <strong className="text-ink">mehr</strong> als nachts. Deshalb entscheidet
              VoltSurfer nicht nach Uhrzeit, sondern jeden Tag neu nach den Börsenpreisen
              für morgen.
            </p>

            <div className="mt-12 lg:mt-16">
              <PriceDay />
            </div>

            <dl className="mt-12 grid gap-6 border-t border-line pt-8 sm:grid-cols-3">
              {[BLOCK_MITTEL.mittag, BLOCK_MITTEL.nacht, BLOCK_MITTEL.abend].map((b, i) => (
                <div key={b.zeit}>
                  <dt className="text-sm font-semibold text-ink-soft">
                    {["Mittag", "Nacht", "Abend"][i]} · {b.zeit}
                  </dt>
                  <dd
                    className={`num mt-1 font-mono text-3xl font-semibold ${
                      i === 2 ? "text-coral" : "text-volt"
                    }`}
                  >
                    {b.ct.toString().replace(".", ",")} ct
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 text-sm text-ink-soft">
              Ø der letzten 12 Monate ({ZEITRAUM}). Der Abend ist{" "}
              {ECKZAHLEN.abendFaktor.toString().replace(".", ",")}-mal so teuer wie der
              Mittag.
            </p>
          </div>
        </section>

        {/* ------------------------------------------------ Negativpreise */}
        <NegativeDays />

        {/* ------------------------------------------------ Verwertungskette */}
        <ValueChain />

        {/* ------------------------------------------------ Einwände */}
        <section className="bg-mist py-20 lg:py-32">
          <div className="mx-auto max-w-6xl px-6 lg:px-8">
            <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
              Was du dich vielleicht gerade fragst
            </h2>
            <div className="mt-12 grid gap-6 md:grid-cols-2">
              {EINWAENDE.map((e) => (
                <article key={e.frage} className="rounded-3xl bg-paper p-7">
                  <h3 className="font-display text-lg font-bold text-ink">
                    &bdquo;{e.frage}&ldquo;
                  </h3>
                  <p className="mt-2 leading-relaxed text-ink-soft text-pretty">{e.antwort}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------ Dynamischer Tarif */}
        <section id="tarif" className="scroll-mt-24 py-20 lg:py-32">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 lg:grid-cols-2 lg:px-8">
            <div>
              <p className="inline-block rounded-full bg-volt-wash px-4 py-1.5 text-sm font-bold text-volt">
                Das passende Fundament
              </p>
              <h2 className="mt-5 max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
                Dynamischer Stromtarif — der Schlüssel zum Ganzen
              </h2>
              <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-ink-soft text-pretty">
                Damit dein Speicher zu Börsenpreisen einkaufen kann, brauchst du einen
                Tarif, der diese Preise an dich weitergibt. Das ist kein Exot mehr — nur
                ein Tarif mit stündlichen Preisen statt einem Festpreis.
              </p>
              <ul className="mt-6 space-y-4">
                {[
                  {
                    t: "Wir richten alles ein",
                    d: "Tarifwechsel, Smart-Meter-Antrag, Anmeldung beim Netzbetreiber — das übernehmen wir im Zuge der Installation.",
                  },
                  {
                    t: "Du bleibst frei",
                    d: "VoltSurfer funktioniert mit jedem dynamischen Tarif. Kein Anbieterzwang, kein Kleingedrucktes.",
                  },
                  {
                    t: "Bald auch direkt von uns",
                    d: "Wir arbeiten an einem eigenen VoltSurfer-Stromtarif — ein Ansprechpartner für Speicher, Steuerung und Strom.",
                  },
                ].map((p) => (
                  <li key={p.t} className="flex gap-4">
                    <span
                      className="mt-1 grid size-6 shrink-0 place-items-center rounded-full bg-volt text-sm font-bold text-white"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                    <div>
                      <p className="font-bold text-ink">{p.t}</p>
                      <p className="leading-relaxed text-ink-soft text-pretty">{p.d}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-3xl border border-line bg-paper p-8">
              <p className="font-mono text-xs font-semibold uppercase tracking-widest text-ink-soft">
                Dieselbe Kilowattstunde, vier Preise
              </p>
              <div className="mt-6 space-y-5">
                {[
                  { label: "Festpreistarif, immer", ct: ENDKUNDE.festpreis, breite: "88%", teuer: true, dezent: true },
                  { label: "Dynamisch — Abendspitze", ct: ENDKUNDE.abendspitze, breite: "100%", teuer: true, dezent: false },
                  { label: "Dynamisch — nachts", ct: ENDKUNDE.nachts, breite: "65%", teuer: false, dezent: false },
                  { label: "Dynamisch — Mittagsstunden", ct: ENDKUNDE.mittags, breite: "55%", teuer: false, dezent: false },
                ].map((b) => (
                  <div key={b.label}>
                    <div className="flex items-baseline justify-between gap-4">
                      <span className="text-sm font-semibold text-ink">{b.label}</span>
                      <span
                        className={`num font-mono text-sm font-semibold ${
                          b.teuer ? "text-coral" : "text-volt"
                        }`}
                      >
                        ~{b.ct} ct
                      </span>
                    </div>
                    <div
                      className={`mt-1.5 h-3.5 rounded-full ${
                        b.dezent ? "bg-ink/20" : b.teuer ? "bg-coral/70" : "bg-volt"
                      }`}
                      style={{ width: b.breite }}
                    />
                  </div>
                ))}
              </div>
              <p className="mt-6 rounded-2xl bg-sky px-5 py-4 text-sm leading-relaxed text-ink-soft text-pretty">
                <strong className="text-ink">Warum stehen hier andere Zahlen?</strong> Auf
                dieser Seite siehst du sonst reine Börsenpreise. Was du zahlst, ist der
                Börsenpreis <em>plus</em> Netzentgelte, Umlagen und Steuern — das ist der
                Unterschied zwischen den {BLOCK_MITTEL.mittag.ct.toString().replace(".", ",")}{" "}
                Cent weiter oben und den {ENDKUNDE.mittags} Cent hier.
              </p>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------ Demo */}
        <section id="demo" className="scroll-mt-24 bg-night py-20 text-white lg:py-32">
          <div className="mx-auto max-w-6xl px-6 lg:px-8">
            <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
              Was hätte <span className="text-volt-bright">dein Haus</span> gespart?
            </h2>
            <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-white/70 text-pretty">
              Fünf Fragen zu deinem Haushalt — danach rechnet die Simulation die letzten
              zwölf Monate mit den echten Börsenpreisen durch, Tag für Tag.
            </p>

            {DEMO_URL ? (
              <div className="mt-12 overflow-hidden rounded-3xl bg-paper">
                <iframe
                  src={DEMO_URL}
                  title="VoltSurfer — Ersparnis berechnen"
                  className="h-[780px] w-full border-0"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="mt-12 rounded-3xl border-2 border-dashed border-white/20 p-12 text-center">
                <p className="font-display text-2xl font-bold">Der Rechner geht bald online.</p>
                <p className="mx-auto mt-3 max-w-md leading-relaxed text-white/70 text-pretty">
                  Bis dahin rechnen wir dir deine Ersparnis gerne persönlich vor — mit
                  deinen echten Verbrauchswerten.
                </p>
                <a
                  href="#kontakt"
                  className="mt-8 inline-block touch-manipulation rounded-full bg-volt-bright px-7 py-4 text-lg font-bold text-night transition-opacity hover:opacity-90"
                >
                  Termin vereinbaren
                </a>
              </div>
            )}
          </div>
        </section>

        {/* ------------------------------------------------ Produkte */}
        <section className="mx-auto max-w-6xl px-6 py-20 lg:px-8 lg:py-32">
          <h2 className="max-w-[20ch] font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
            Zwei Größen, ein System
          </h2>
          <p className="mt-5 max-w-[65ch] text-lg leading-relaxed text-ink-soft text-pretty">
            Welche zu dir passt, hängt vom Verbrauch ab — das klären wir im Gespräch.
          </p>

          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {[
              {
                name: "VoltSurfer 20",
                kwh: "20 kWh",
                preis: "8.000 €",
                fuer: "Für Haushalte bis etwa 12 kWh Tagesbedarf",
                merkmale: [
                  "11 kW laden und entladen",
                  "LFP-Zellen mit 6.000 Ladezyklen",
                  "§ 14a-fähig für reduzierte Netzentgelte",
                ],
                hervor: false,
              },
              {
                name: "VoltSurfer 30",
                kwh: "30 kWh",
                preis: "11.000 €",
                fuer: "Für Wärmepumpe, E-Auto oder größeren Haushalt",
                merkmale: [
                  "11 kW laden und entladen",
                  "LFP-Zellen mit 6.000 Ladezyklen",
                  "Mehr Handelsvolumen — höherer Ertrag",
                ],
                hervor: true,
              },
            ].map((p) => (
              <article
                key={p.name}
                className={`rounded-3xl border-2 bg-paper p-8 ${
                  p.hervor ? "border-volt shadow-lg" : "border-line"
                }`}
              >
                {p.hervor && (
                  <span className="mb-4 inline-block rounded-full bg-volt px-3.5 py-1 font-mono text-xs font-bold uppercase tracking-wide text-white">
                    Meist gewählt
                  </span>
                )}
                <h3 className="font-display text-2xl font-extrabold">{p.name}</h3>
                <p className="mt-1 text-ink-soft">{p.fuer}</p>
                <p className="num mt-6 font-mono text-5xl font-semibold text-volt">{p.preis}</p>
                <p className="mt-1 text-ink-soft">{p.kwh} nutzbare Kapazität</p>
                <ul className="mt-7 space-y-3">
                  {p.merkmale.map((m) => (
                    <li key={m} className="flex gap-3">
                      <span
                        className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-volt-wash text-xs font-bold text-volt"
                        aria-hidden="true"
                      >
                        ✓
                      </span>
                      <span className="text-ink-soft">{m}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <p className="mt-8 rounded-3xl bg-sun-wash px-6 py-5 leading-relaxed text-ink-soft text-pretty">
            <strong className="text-ink">Zu den Preisen:</strong> Das sind Richtwerte für
            die Anlage inklusive Standardinstallation. Was es bei dir tatsächlich kostet,
            hängt vom Gebäude ab — muss zum Beispiel der Zählerschrank erneuert werden,
            kommt Aufwand hinzu. Du bekommst vor der Bestellung ein verbindliches Angebot
            ohne versteckte Posten.
          </p>
        </section>

        {/* ------------------------------------------------ FAQ */}
        <section id="faq" className="scroll-mt-24 bg-mist py-20 lg:py-32">
          <div className="mx-auto max-w-4xl px-6 lg:px-8">
            <h2 className="font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
              Häufige Fragen
            </h2>
            <Faq />
          </div>
        </section>

        {/* ------------------------------------------------ Kontakt */}
        <section id="kontakt" className="scroll-mt-24 py-20 lg:py-32">
          <div className="mx-auto max-w-3xl px-6 lg:px-8">
            <h2 className="font-display text-[clamp(2rem,4vw,2.75rem)] font-extrabold leading-[1.1] text-balance">
              Wir rechnen es dir vor
            </h2>
            <p className="mt-5 text-lg leading-relaxed text-ink-soft text-pretty">
              Am besten bei dir zu Hause: Wir schauen uns deinen Zählerschrank an, nehmen
              deine echten Verbrauchswerte und zeigen dir schwarz auf weiß, was sich
              rechnet — und was nicht. Kostenlos und unverbindlich.
            </p>
            <div className="mt-12">
              <ContactForm />
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-mist py-12">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 sm:flex-row sm:items-start sm:justify-between lg:px-8">
          <div>
            <Logo className="text-lg" />
            <p className="mt-2 text-ink-soft">Dein Speicher surft die Strompreiswelle</p>
          </div>
          <nav className="flex gap-8 text-sm font-semibold text-ink-soft">
            <a href="/impressum" className="hover:text-ink">
              Impressum
            </a>
            <a href="/datenschutz" className="hover:text-ink">
              Datenschutz
            </a>
          </nav>
        </div>
        <p className="mx-auto mt-10 max-w-6xl px-6 text-xs leading-relaxed text-ink-soft/80 text-pretty lg:px-8">
          Alle Preisangaben beruhen auf den Day-Ahead-Börsenpreisen DE-LU im Zeitraum{" "}
          {ZEITRAUM} (Quelle: energy-charts.info / SMARD, Bundesnetzagentur).
          Ersparnisangaben stammen aus Simulationen mit diesen Preisen und
          Standardlastprofilen; der Anteil aus der Netzvermarktung setzt den Betrieb des
          VoltSurfer-Verbunds voraus. Dein tatsächliches Ergebnis hängt von Verbrauch,
          Tarif, Netzentgelten und den regulatorischen Rahmenbedingungen ab — insbesondere
          von der noch ausstehenden Abgrenzungsfestlegung der Bundesnetzagentur zum
          Speicherprivileg (§ 21 EnFG, § 118 EnWG).
        </p>
      </footer>
    </>
  );
}
