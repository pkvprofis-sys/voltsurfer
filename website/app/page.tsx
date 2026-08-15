import {
  BatteryCharging,
  Coffee,
  CookingPot,
  PiggyBank,
  Receipt,
  Sparkles,
  Sun,
  Unlock,
} from "lucide-react";

import { AppPreview } from "@/components/AppPreview";
import { ContactForm } from "@/components/ContactForm";
import { Faq } from "@/components/Faq";
import { HeroWave } from "@/components/HeroWave";
import { Logo } from "@/components/Logo";

const DEMO_URL = process.env.NEXT_PUBLIC_DEMO_URL;

/* Ein echter Tag aus der Simulation — Uhrzeiten und Preise wie sie die
   Börse liefert. Die Tagesbilanz 3,69 € × 365 ≈ 1.348 €/Jahr. */
const TAGESVERLAUF = [
  {
    zeit: "02:15",
    icon: BatteryCharging,
    titel: "Der Speicher kauft ein",
    text: "Börsenpreis 8,4 Cent. In den günstigsten Stunden der Nacht lädt VoltSurfer mit 11 kW — an manchen Tagen gibt es fürs Laden sogar Geld, wenn der Preis ins Minus rutscht.",
    preis: "8,4 ct",
    teuer: false,
  },
  {
    zeit: "06:50",
    icon: Coffee,
    titel: "Duschen, Kaffee, Wärmepumpe",
    text: "Der Morgen läuft komplett aus dem Speicher. Im Netz kostet Strom jetzt schon wieder das Dreifache — dich betrifft das nicht.",
    preis: "aus dem Speicher",
    teuer: false,
  },
  {
    zeit: "13:10",
    icon: Sun,
    titel: "Die Mittagsdelle",
    text: "Viel Solarstrom im Netz drückt den Preis ein zweites Mal. Wenn der Abend lang wird, lädt der Speicher hier günstig nach.",
    preis: "11,2 ct",
    teuer: false,
  },
  {
    zeit: "18:45",
    icon: CookingPot,
    titel: "Feierabend, Herd an",
    text: "Ganz Deutschland kocht — die Kilowattstunde kostet jetzt 38 Cent. Du kochst mit dem Strom von heute Nacht.",
    preis: "38 ct — zahlst du nicht",
    teuer: true,
  },
  {
    zeit: "23:59",
    icon: Receipt,
    titel: "Tagesbilanz: 3,69 € gespart",
    text: "Kein Knopfdruck, keine App-Pflicht. Morgen um kurz nach Mitternacht macht der Speicher einfach weiter.",
    preis: "× 365 Tage",
    teuer: false,
  },
];

const EINWAENDE = [
  {
    frage: "Geht das auf die Batterie?",
    antwort:
      "Wir rechnen den Verschleiß mit ein. Ein Ladezyklus wird nur gefahren, wenn er sich nach Abzug der Batteriealterung lohnt. Die LFP-Zellen halten 6.000 Zyklen — bei dieser Fahrweise über 13 Jahre.",
  },
  {
    frage: "Muss ich mich darum kümmern?",
    antwort:
      "Nein. Die Steuerung plant jede Nacht neu, mit Börsenpreisen und Wettervorhersage. Du kannst zuschauen, wenn du magst — musst aber nichts einstellen.",
  },
  {
    frage: "Und wenn ich schon PV habe?",
    antwort:
      "Dann hat dein Solarstrom immer Vorrang. Der Speicher wird nur so weit aus dem Netz geladen, wie am nächsten Tag Platz bleibt — die Sonnenprognose fließt in die Planung ein.",
  },
  {
    frage: "Bleibt meine Garantie bestehen?",
    antwort:
      "Ja. Der Speicher läuft innerhalb seiner Herstellerspezifikation — Ladeleistung, Temperatur und Entladetiefe bleiben im schonenden Bereich.",
  },
];

export default function Home() {
  return (
    <>
      <header className="sticky top-0 z-50 border-b border-white/10 bg-night/85 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <a href="#top" aria-label="VoltSurfer — zur Startseite">
            <Logo className="text-xl text-white" dark />
          </a>
          <div className="flex items-center gap-6">
            <a
              href="#tag"
              className="hidden text-sm font-semibold text-white/70 hover:text-white sm:block"
            >
              So funktioniert&apos;s
            </a>
            <a
              href="#faq"
              className="hidden text-sm font-semibold text-white/70 hover:text-white sm:block"
            >
              Fragen
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
        {/* ------------------------------------------------ Hero: die Nacht */}
        <section className="relative overflow-hidden bg-night text-white">
          <HeroWave className="opacity-90" />
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-b from-night/60 via-transparent to-night"
            aria-hidden="true"
          />

          <div className="relative mx-auto grid min-h-[82svh] max-w-6xl content-center items-center gap-12 px-5 py-24 lg:grid-cols-[1fr_auto]">
            <div>
            <p className="animate-rise font-mono text-sm font-semibold tracking-widest text-volt-bright">
              02:15 UHR · DEIN SPEICHER KAUFT GERADE EIN
            </p>
            <h1 className="mt-5 max-w-3xl animate-rise font-display text-5xl font-extrabold leading-[1.02] tracking-tight text-balance sm:text-7xl">
              Nachts kostet Strom 8&nbsp;Cent.
              <br />
              Abends&nbsp;38.
            </h1>
            <p className="mt-6 max-w-xl animate-rise text-lg leading-relaxed text-white/75 text-pretty sm:text-xl">
              Dein Speicher kennt den Unterschied — er kauft, wenn Strom fast nichts
              kostet, und versorgt dein Haus, wenn alle anderen teuer zahlen.{" "}
              <strong className="text-white">
                Bis zu <span className="font-mono text-volt-bright">1.348&nbsp;€</span> im
                Jahr.
              </strong>
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
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

            <dl className="mt-12 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/10 pt-6 font-mono text-sm text-white/60">
              <div>
                <dt className="inline">Ø Preisspanne pro Tag&nbsp;</dt>
                <dd className="inline font-semibold text-white">&gt;14 ct/kWh</dd>
              </div>
              <div>
                <dt className="inline">Viertelstunden im Minus&nbsp;</dt>
                <dd className="inline font-semibold text-white">~7 %</dd>
              </div>
              <div>
                <dt className="inline">Laden &amp; Entladen&nbsp;</dt>
                <dd className="inline font-semibold text-white">11 kW</dd>
              </div>
            </dl>
            </div>

            <AppPreview className="animate-rise justify-self-center lg:justify-self-end" />
          </div>
        </section>

        {/* ------------------------------------------------ Leise Vorteilszeile */}
        <section className="border-b border-line">
          <div className="mx-auto grid max-w-6xl gap-6 px-5 py-8 sm:grid-cols-3">
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

        {/* ------------------------------------------------ Ein Tag mit VoltSurfer */}
        <section id="tag" className="scroll-mt-24 py-16 lg:py-24">
          <div className="mx-auto max-w-6xl px-5">
            <h2 className="max-w-2xl font-display text-3xl font-extrabold leading-tight text-balance sm:text-5xl">
              Ein ganz normaler Dienstag
            </h2>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-ink-soft text-pretty">
              Kein Zukunftsversprechen — so sieht ein Tag aus, wenn ein Speicher die
              Börsenpreise kennt. Die Preise stammen aus unserer Simulation mit echten
              Marktdaten.
            </p>

            <ol className="relative mt-12 max-w-3xl space-y-0 border-l-2 border-line pl-0">
              {TAGESVERLAUF.map((t) => (
                <li key={t.zeit} className="relative pb-10 pl-8 last:pb-0 sm:pl-12">
                  <span
                    className={`absolute -left-[13px] grid size-6 place-items-center rounded-full border-2 border-paper ${
                      t.teuer ? "bg-coral" : "bg-volt"
                    }`}
                    aria-hidden="true"
                  />
                  <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                    <time className="font-mono text-lg font-semibold text-ink">{t.zeit}</time>
                    <span
                      className={`rounded-full px-3 py-0.5 font-mono text-xs font-semibold ${
                        t.teuer ? "bg-coral/10 text-coral" : "bg-volt-wash text-volt"
                      }`}
                    >
                      {t.preis}
                    </span>
                  </div>
                  <h3 className="mt-2 flex items-center gap-2.5 font-display text-xl font-bold">
                    <t.icon className="size-5 text-ink-soft" aria-hidden="true" />
                    {t.titel}
                  </h3>
                  <p className="mt-1.5 max-w-xl leading-relaxed text-ink-soft text-pretty">
                    {t.text}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ------------------------------------------------ Einwände */}
        <section className="bg-mist py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-5">
            <h2 className="max-w-2xl font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
              Was du dich vielleicht gerade fragst
            </h2>
            <div className="mt-10 grid gap-6 md:grid-cols-2">
              {EINWAENDE.map((e) => (
                <article key={e.frage} className="rounded-2xl bg-paper p-7">
                  <h3 className="font-display text-lg font-bold text-ink">
                    &bdquo;{e.frage}&ldquo;
                  </h3>
                  <p className="mt-2 leading-relaxed text-ink-soft text-pretty">{e.antwort}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------ Dynamischer Stromtarif */}
        <section id="tarif" className="scroll-mt-24 py-16 lg:py-20">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 lg:grid-cols-2">
            <div>
              <p className="inline-block rounded-full bg-volt-wash px-4 py-1.5 text-sm font-bold text-volt">
                Das passende Fundament
              </p>
              <h2 className="mt-5 font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
                Dynamischer Stromtarif — der Schlüssel zum Ganzen
              </h2>
              <p className="mt-4 text-lg leading-relaxed text-ink-soft text-pretty">
                Damit dein Speicher zu Börsenpreisen einkaufen kann, brauchst du einen
                Tarif, der diese Preise an dich weitergibt. Das ist kein Exot mehr —
                nur ein Tarif mit stündlichen Preisen statt einem Festpreis.
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
                    d: "Wir arbeiten an einem eigenen VoltSurfer-Stromtarif — ein Ansprechpartner für Speicher, Steuerung und Strom. Bestandskunden steigen zuerst ein.",
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

            <div className="rounded-2xl border border-line bg-paper p-8">
              <p className="font-mono text-xs font-semibold uppercase tracking-widest text-ink-soft">
                Dieselbe Kilowattstunde, vier Preise
              </p>
              <div className="mt-6 space-y-5">
                {[
                  { label: "Festpreistarif, immer", preis: "~35 ct", breite: "92%", teuer: true, dezent: true },
                  { label: "Dynamisch — Abendspitze", preis: "~40 ct", breite: "100%", teuer: true, dezent: false },
                  { label: "Dynamisch — nachts", preis: "~18 ct", breite: "45%", teuer: false, dezent: false },
                  { label: "Dynamisch — beste Stunden", preis: "~12 ct", breite: "30%", teuer: false, dezent: false },
                ].map((b) => (
                  <div key={b.label}>
                    <div className="flex items-baseline justify-between gap-4">
                      <span className="text-sm font-semibold text-ink">{b.label}</span>
                      <span
                        className={`font-mono text-sm font-semibold ${
                          b.teuer ? "text-coral" : "text-volt"
                        }`}
                      >
                        {b.preis}
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
              <p className="mt-6 text-sm leading-relaxed text-ink-soft text-pretty">
                Ohne Speicher ist der dynamische Tarif ein Glücksspiel — du kochst nun mal
                abends. <strong className="text-ink">Mit</strong> Speicher wird gekauft,
                wenn es günstig ist, und verbraucht, wann du willst. Beispielwerte inkl.
                Steuern und Abgaben.
              </p>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------ Live-Demo (Nacht-Sektion) */}
        <section id="demo" className="scroll-mt-24 bg-night py-16 text-white lg:py-20">
          <div className="mx-auto max-w-6xl px-5">
            <h2 className="max-w-2xl font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
              Was hätte <span className="text-volt-bright">dein Haus</span> gespart?
            </h2>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/70 text-pretty">
              Fünf Fragen zu deinem Haushalt — danach rechnet die Simulation die letzten
              zwölf Monate mit den echten Börsenpreisen durch, Tag für Tag.
            </p>

            {DEMO_URL ? (
              <div className="mt-10 overflow-hidden rounded-2xl bg-paper">
                <iframe
                  src={DEMO_URL}
                  title="VoltSurfer — Ersparnis berechnen"
                  className="h-[780px] w-full border-0"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="mt-10 rounded-2xl border-2 border-dashed border-white/20 p-12 text-center">
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
        <section className="mx-auto max-w-6xl px-5 py-16 lg:py-24">
          <h2 className="font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
            Zwei Größen, ein System
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-ink-soft text-pretty">
            Welche zu dir passt, hängt vom Verbrauch ab — das klären wir im Gespräch.
          </p>

          <div className="mt-10 grid gap-6 md:grid-cols-2">
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
                className={`rounded-2xl border-2 bg-paper p-8 ${
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
                <p className="mt-6 font-mono text-5xl font-semibold text-volt">{p.preis}</p>
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

          <p className="mt-8 rounded-2xl bg-sun/10 px-6 py-5 leading-relaxed text-ink-soft text-pretty">
            <strong className="text-ink">Zu den Preisen:</strong> Das sind Richtwerte für
            die Anlage inklusive Standardinstallation. Was es bei dir tatsächlich kostet,
            hängt vom Gebäude ab — muss zum Beispiel der Zählerschrank erneuert werden,
            kommt Aufwand hinzu. Du bekommst vor der Bestellung ein verbindliches Angebot
            ohne versteckte Posten.
          </p>
        </section>

        {/* ------------------------------------------------ FAQ */}
        <section id="faq" className="scroll-mt-24 bg-mist py-16 lg:py-20">
          <div className="mx-auto max-w-4xl px-5">
            <h2 className="font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
              Häufige Fragen
            </h2>
            <Faq />
          </div>
        </section>

        {/* ------------------------------------------------ Kontakt */}
        <section id="kontakt" className="scroll-mt-24 py-16 lg:py-24">
          <div className="mx-auto max-w-3xl px-5">
            <h2 className="font-display text-3xl font-extrabold leading-tight text-balance sm:text-4xl">
              Wir rechnen es dir vor
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-ink-soft text-pretty">
              Am besten bei dir zu Hause: Wir schauen uns deinen Zählerschrank an, nehmen
              deine echten Verbrauchswerte und zeigen dir schwarz auf weiß, was sich
              rechnet — und was nicht. Kostenlos und unverbindlich.
            </p>
            <div className="mt-10">
              <ContactForm />
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-mist py-12">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 sm:flex-row sm:items-start sm:justify-between">
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
        <p className="mx-auto mt-10 max-w-6xl px-5 text-xs leading-relaxed text-ink-soft/80 text-pretty">
          Ersparnisangaben beruhen auf Simulationen mit historischen Day-Ahead-Preisen
          (Quelle: energy-charts.info / SMARD, Bundesnetzagentur) und Standardlastprofilen.
          Dein tatsächliches Ergebnis hängt von Verbrauch, Tarif, Netzentgelten und den
          regulatorischen Rahmenbedingungen ab.
        </p>
      </footer>
    </>
  );
}
