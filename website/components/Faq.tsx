import { ECKZAHLEN, ERSPARNIS, NEGATIV } from "@/lib/preise";

const FRAGEN = [
  {
    frage: "Woher weiß der Speicher, wann Strom günstig ist?",
    antwort:
      "Der Börsenstrompreis für den nächsten Tag steht jeden Mittag gegen 13 Uhr fest — für jede Viertelstunde einzeln. VoltSurfer holt sich diese Preise automatisch und plant daraus den Fahrplan. Dazu kommt die Wettervorhersage, damit auch der Wärmepumpen-Bedarf richtig eingeplant wird.",
  },
  {
    frage: "Stimmt es, dass Strom im Winter mittags teurer ist als nachts?",
    antwort:
      "Ja. Von November bis Januar liefert die Sonne zu wenig, um den Mittagspreis zu drücken — dann kostet die Kilowattstunde mittags rund 3 Cent mehr als nachts. Genau deshalb arbeitet die Steuerung nicht mit festen Uhrzeiten: Sie sucht sich jeden Tag neu die günstigsten Viertelstunden, egal ob die um 13 oder um 3 Uhr liegen.",
  },
  {
    frage: "Was ist der VoltSurfer-Verbund?",
    antwort:
      "Ein virtuelles Kraftwerk: Viele Speicher werden zusammengeschaltet und treten gemeinsam an der Strombörse auf — einzeln wäre eine Hausanlage dafür zu klein. Dafür brauchen wir rund 20 bis 30 Haushalte. Läuft der Verbund, verkauft dein Speicher überschüssige Energie zu Höchstpreisen. Am Handel selbst musst du nichts tun; die Erlöse erscheinen auf deiner Abrechnung.",
  },
  {
    frage: "Brauche ich dafür eine Photovoltaik-Anlage?",
    antwort:
      "Nein. VoltSurfer funktioniert auch ganz ohne Solaranlage — er lebt vom Preisunterschied zwischen den Stunden, nicht von der eigenen Sonne. Wenn du eine PV-Anlage hast, wird sie eingebunden: Dein Solarstrom hat immer Vorrang vor Netzstrom.",
  },
  {
    frage: "Lohnt sich das auch an schlechten Tagen?",
    antwort: `An ${ECKZAHLEN.tageUeber10ct} % aller Tage liegen mehr als 10 Cent zwischen der günstigsten und der teuersten Stunde — im Schnitt sind es ${ECKZAHLEN.tagesspanne.toString().replace(".", ",")} Cent. Ausreißer nach unten gibt es auch: Der tiefste je gemessene Preis lag bei minus 50 Cent je Kilowattstunde. Auf solche Extremtage kommt es aber nicht an; die Rechnung trägt sich über den Durchschnitt.`,
  },
  {
    frage: "Was, wenn die Strompreise sich ändern?",
    antwort: `Der Speicher verdient am Unterschied zwischen günstigen und teuren Stunden, nicht am Preisniveau. Diese Spanne ist in den letzten Jahren gewachsen, weil immer mehr Wind- und Solarstrom im Netz ist: Der Anteil der Viertelstunden mit negativem Preis stieg von ${NEGATIV.trend[0].anteil.toString().replace(".", ",")} % im Jahr 2023 auf ${NEGATIV.trend[3].anteil.toString().replace(".", ",")} % in 2026.`,
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
    antwort: `Nichts Zusätzliches. Du zahlst deinen Stromtarif wie bisher — nur deutlich weniger, weil ein Großteil deines Verbrauchs aus günstig geladenem Strom kommt. Gerechnet haben wir mit rund ${ERSPARNIS.heute} € Ersparnis im ersten Jahr, noch ohne die spätere Vermarktung. Das Energiemanagement läuft auf einem Gerät bei dir zu Hause, ohne monatliche Gebühr.`,
  },
];

export function Faq() {
  return (
    <div className="mt-12 divide-y divide-line rounded-3xl border border-line bg-paper">
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
          <p className="mt-3 max-w-[65ch] leading-relaxed text-ink-soft text-pretty">
            {f.antwort}
          </p>
        </details>
      ))}
    </div>
  );
}
