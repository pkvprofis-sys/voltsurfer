import { Logo } from "@/components/Logo";

export const metadata = { title: "Impressum — VoltSurfer" };

export default function Impressum() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-14">
      <a href="/" className="rounded">
        <Logo className="text-lg" />
      </a>

      <div className="mt-6 rounded-xl border border-sun/50 bg-sun/10 px-5 py-4 text-sm leading-relaxed text-ink">
        <strong>Noch auszufüllen:</strong> Diese Seite enthält Platzhalter. Ein
        vollständiges Impressum ist nach §&nbsp;5 DDG (früher TMG) Pflicht — fehlende
        oder falsche Angaben sind abmahnfähig. Bitte alle eckigen Klammern durch Ihre
        echten Daten ersetzen und im Zweifel rechtlich prüfen lassen.
      </div>

      <h1 className="mt-8 text-3xl font-bold">Impressum</h1>

      <section className="mt-8 space-y-6 leading-relaxed text-ink-soft">
        <div>
          <h2 className="text-lg font-bold text-ink">Angaben gemäß § 5 DDG</h2>
          <p className="mt-2">
            [Firmenname]
            <br />
            [Straße und Hausnummer]
            <br />
            [PLZ und Ort]
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">Vertreten durch</h2>
          <p className="mt-2">[Vor- und Nachname der vertretungsberechtigten Person]</p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">Kontakt</h2>
          <p className="mt-2">
            Telefon: [Telefonnummer]
            <br />
            E-Mail: [E-Mail-Adresse]
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">Registereintrag</h2>
          <p className="mt-2">
            Registergericht: [Amtsgericht]
            <br />
            Registernummer: [HRB-Nummer]
            <br />
            <span className="text-ink-soft/70">(entfällt bei Einzelunternehmen)</span>
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">Umsatzsteuer-ID</h2>
          <p className="mt-2">
            Umsatzsteuer-Identifikationsnummer gemäß § 27&nbsp;a UStG: [USt-IdNr.]
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">
            Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV
          </h2>
          <p className="mt-2">
            [Vor- und Nachname]
            <br />
            [Anschrift]
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">Streitschlichtung</h2>
          <p className="mt-2">
            Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor
            einer Verbraucherschlichtungsstelle teilzunehmen.
          </p>
        </div>
      </section>

      <a href="/" className="mt-10 inline-block text-volt underline underline-offset-4">
        Zurück zur Startseite
      </a>
    </main>
  );
}
