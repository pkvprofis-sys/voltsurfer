const FRAGEN = [
  {
    frage: "Woher weiß der Speicher, wann Strom günstig ist?",
    antwort:
      "Der Börsenstrompreis für den nächsten Tag steht jeden Mittag gegen 13 Uhr fest — für jede Viertelstunde einzeln. VoltSurfer holt sich diese Preise automatisch und plant daraus den Fahrplan für den nächsten Tag. Dazu kommt die Wettervorhersage, damit auch der Wärmepumpen-Bedarf richtig eingeplant wird.",
  },
  {
    frage: "Brauche ich dafür eine Photovoltaik-Anlage?",
    antwort:
      "Nein. VoltSurfer funktioniert auch ganz ohne Solaranlage — er lebt vom Preisunterschied zwischen Tag und Nacht, nicht von der Sonne. Wenn du eine PV-Anlage hast, wird sie natürlich mit eingebunden: Dein Solarstrom hat immer Vorrang vor Netzstrom.",
  },
  {
    frage: "Was, wenn die Strompreise sich ändern?",
    antwort:
      "Der Speicher verdient am Unterschied zwischen günstigen und teuren Stunden, nicht am absoluten Preisniveau. Diese Spanne ist in den letzten Jahren eher gewachsen, weil immer mehr Wind- und Solarstrom im Netz ist. Mittlerweile gibt es an rund 7 % aller Viertelstunden sogar negative Preise — da bekommst du fürs Laden Geld.",
  },
  {
    frage: "Was brauche ich für einen dynamischen Stromtarif?",
    antwort:
      "Ein intelligentes Messsystem (Smart Meter). Seit 2025 hat jeder Haushalt darauf Anspruch, bei Wärmepumpe oder Speicher über 4,2 kW ist der Einbau ohnehin vorgesehen. Wir sagen dir im Beratungsgespräch, was in deinem Fall nötig ist, und begleiten die Anmeldung.",
  },
  {
    frage: "Bleibt die Herstellergarantie bestehen?",
    antwort:
      "Ja. Der Speicher wird innerhalb seiner Spezifikationen betrieben — Ladeleistung, Temperaturgrenzen und Entladetiefe halten wir bewusst schonend ein. Die Steuerung rechnet den Verschleiß sogar mit ein: Ein Ladezyklus wird nur gefahren, wenn er sich nach Abzug der Batteriealterung lohnt.",
  },
  {
    frage: "Wie lange dauert der Einbau?",
    antwort:
      "Die Installation selbst dauert in der Regel einen Tag. Vorher schauen wir uns bei einem Termin vor Ort deinen Zählerschrank und den Anschlussraum an — daraus ergibt sich, ob zusätzliche Arbeiten nötig sind. Die Anmeldung beim Netzbetreiber übernehmen wir.",
  },
  {
    frage: "Was kostet mich das im laufenden Betrieb?",
    antwort:
      "Nichts Zusätzliches. Du zahlst deinen Stromtarif wie bisher — nur eben deutlich weniger, weil ein Großteil deines Verbrauchs aus günstig geladenem Strom kommt. Das Energiemanagement läuft auf einem Gerät bei dir zu Hause, ohne monatliche Gebühr.",
  },
];

export function Faq() {
  return (
    <div className="mt-10 divide-y divide-line rounded-3xl border border-line bg-paper">
      {FRAGEN.map((f) => (
        <details key={f.frage} className="group px-6 py-5 sm:px-8">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-lg font-bold text-ink">
            {f.frage}
            <span
              aria-hidden="true"
              className="grid size-8 shrink-0 place-items-center rounded-full bg-volt-wash text-xl leading-none text-volt transition-transform group-open:rotate-45"
            >
              +
            </span>
          </summary>
          <p className="mt-3 max-w-3xl leading-relaxed text-ink-soft text-pretty">{f.antwort}</p>
        </details>
      ))}
    </div>
  );
}
