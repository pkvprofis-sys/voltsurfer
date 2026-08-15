import { Logo } from "@/components/Logo";

export const metadata = { title: "Datenschutzerklärung — VoltSurfer" };

export default function Datenschutz() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-14">
      <a href="/" className="rounded">
        <Logo className="text-lg" />
      </a>

      <div className="mt-6 rounded-xl border border-sun/50 bg-sun/10 px-5 py-4 text-sm leading-relaxed text-ink">
        <strong>Noch auszufüllen:</strong> Dieser Entwurf beschreibt bereits korrekt, was
        die Website technisch tut (Kontaktformular in Supabase, Hosting bei Vercel).
        Ergänzen Sie Ihre Firmendaten in den eckigen Klammern und lassen Sie den Text vor
        dem Livegang juristisch prüfen — eine unvollständige Datenschutzerklärung ist
        abmahnfähig.
      </div>

      <h1 className="mt-8 text-3xl font-bold">Datenschutzerklärung</h1>

      <section className="mt-8 space-y-6 leading-relaxed text-ink-soft">
        <div>
          <h2 className="text-lg font-bold text-ink">1. Verantwortlicher</h2>
          <p className="mt-2">
            [Firmenname], [Anschrift], [E-Mail-Adresse]. Bei Fragen zum Datenschutz
            wenden Sie sich bitte an die genannte Adresse.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">2. Kontaktformular</h2>
          <p className="mt-2">
            Wenn Sie uns über das Formular eine Anfrage senden, verarbeiten wir die von
            Ihnen eingegebenen Daten (Name, E-Mail-Adresse, optional Telefonnummer,
            Postleitzahl, Angaben zu Ihrem Stromverbrauch und Ihrer Ausstattung sowie
            Ihre Nachricht), um Ihre Anfrage zu beantworten und ein Beratungsangebot zu
            erstellen.
          </p>
          <p className="mt-2">
            Rechtsgrundlage ist Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO) sowie die
            Anbahnung eines Vertragsverhältnisses (Art. 6 Abs. 1 lit. b DSGVO). Sie
            können Ihre Einwilligung jederzeit für die Zukunft widerrufen — eine formlose
            Nachricht an die oben genannte Adresse genügt.
          </p>
          <p className="mt-2">
            Wir speichern Ihre Anfrage, bis der Zweck entfällt, längstens [z.&nbsp;B. 24
            Monate] nach dem letzten Kontakt. Gesetzliche Aufbewahrungsfristen bleiben
            unberührt.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">3. Auftragsverarbeiter</h2>
          <p className="mt-2">
            <strong className="text-ink">Supabase</strong> — Speicherung der
            Formularanfragen in einer Datenbank innerhalb der EU (Region Frankfurt).
            Mit dem Anbieter besteht ein Auftragsverarbeitungsvertrag.
          </p>
          <p className="mt-2">
            <strong className="text-ink">Vercel</strong> — Bereitstellung und
            Auslieferung dieser Website. Dabei werden technisch notwendige Server-Logs
            (IP-Adresse, Zeitpunkt, aufgerufene Seite) verarbeitet, um den Betrieb und
            die Sicherheit zu gewährleisten (Art. 6 Abs. 1 lit. f DSGVO).
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">4. Ersparnis-Rechner</h2>
          <p className="mt-2">
            Der eingebettete Rechner läuft auf einem separaten Dienst. Ihre Eingaben
            dienen ausschließlich der Berechnung im Browser bzw. auf dem Rechenserver und
            werden nicht dauerhaft mit Ihrer Person verknüpft gespeichert, sofern Sie sie
            nicht selbst über das Kontaktformular übermitteln.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">5. Keine Tracking-Cookies</h2>
          <p className="mt-2">
            Diese Website setzt keine Analyse- oder Marketing-Cookies und bindet keine
            externen Werbenetzwerke ein. Es werden nur technisch notwendige Daten
            verarbeitet.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-ink">6. Ihre Rechte</h2>
          <p className="mt-2">
            Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16),
            Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18),
            Datenübertragbarkeit (Art. 20) und Widerspruch (Art. 21). Außerdem können Sie
            sich bei einer Datenschutz-Aufsichtsbehörde beschweren (Art. 77 DSGVO).
          </p>
        </div>
      </section>

      <a href="/" className="mt-10 inline-block text-volt underline underline-offset-4">
        Zurück zur Startseite
      </a>
    </main>
  );
}
