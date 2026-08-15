/**
 * Alle Preiszahlen der Website an einer Stelle.
 *
 * Quelle: Day-Ahead-Börsenpreise DE-LU (energy-charts.info / SMARD), ausgewertet
 * über data_cache/price_*.parquet des VoltSurfer-Repos. Zeitraum 15.08.2025 bis
 * 15.08.2026, 356 Tage. Alle Werte in ct/kWh, netto — also ohne Netzentgelte,
 * Umlagen und Steuern.
 *
 * Zum Aktualisieren: scripts-Analyse über die Parquet-Dateien laufen lassen und
 * die Arrays hier ersetzen. Die Website liest zur Laufzeit keine Messdaten.
 */

export const ZEITRAUM = "15.08.2025 – 15.08.2026";

/** Ø-Preis je Tagesstunde (0–23 Uhr) über die vollen 12 Monate. */
export const PROFIL_JAHR = [
  10.1, 9.6, 9.3, 9.1, 9.2, 9.7, 10.9, 11.9, 11.4, 9.6, 7.7, 6.4,
  5.4, 4.9, 5.4, 6.8, 8.7, 11.1, 13.1, 14.5, 14.3, 13.1, 11.9, 10.6,
];

/** Sommerhalbjahr (April–September): das Tal liegt mittags. */
export const PROFIL_SOMMER = [
  12.3, 11.6, 11.2, 11.1, 11.2, 11.6, 12.7, 12.7, 11.0, 8.3, 5.6, 3.7,
  2.1, 1.0, 1.2, 2.7, 5.0, 8.5, 12.2, 16.2, 18.3, 17.0, 14.9, 13.0,
];

/** Winter (November–Januar): das Tal wandert zurück in die Nacht. */
export const PROFIL_WINTER = [
  8.3, 8.0, 7.7, 7.6, 7.6, 8.0, 9.1, 10.9, 11.9, 11.4, 10.6, 10.2,
  10.0, 10.2, 10.9, 12.1, 13.1, 13.7, 12.9, 11.8, 10.6, 9.8, 9.5, 8.6,
];

export type Saison = "sommer" | "winter";

export const SAISON = {
  sommer: {
    name: "Sommertag",
    profil: PROFIL_SOMMER,
    /** Stunden, in denen typischerweise geladen wird */
    tal: { von: 10, bis: 16 },
    tief: { stunde: 13, ct: 1.0 },
    hoch: { stunde: 20, ct: 18.3 },
    faktor: "18-fach",
    hinweis: "April bis September · an 98 % dieser Tage liegt der Tiefstpreis mittags",
  },
  winter: {
    name: "Wintertag",
    profil: PROFIL_WINTER,
    tal: { von: 1, bis: 6 },
    tief: { stunde: 3, ct: 7.6 },
    hoch: { stunde: 17, ct: 13.7 },
    faktor: "1,8-fach",
    hinweis: "November bis Januar · mittags rund 3 ct teurer als nachts",
  },
} as const;

/** Abendspitze — die einzige Konstante im Jahr. */
export const ABENDSPITZE = { von: 17, bis: 21 };

/** Ø über die 12 Monate, gerundet für die Kennzahlzeile. */
export const BLOCK_MITTEL = {
  mittag: { ct: 5.5, zeit: "11–15 Uhr" },
  nacht: { ct: 9.4, zeit: "0–5 Uhr" },
  abend: { ct: 14.1, zeit: "18–20 Uhr" },
};

export const ECKZAHLEN = {
  /** Anteil der Tage, an denen der Tiefstpreis zwischen 10 und 16 Uhr liegt */
  tiefstpreisMittags: 64,
  tiefstpreisMittagsSommer: 98,
  /** Ø Abstand zwischen teuerster und günstigster Viertelstunde eines Tages */
  tagesspanne: 15.6,
  /** Anteil der Tage mit mehr als 10 ct Spanne */
  tageUeber10ct: 69,
  /** Ø-Preis der zwei günstigsten Stunden eines Tages — der Einkaufspreis */
  einkaufspreis: 3.6,
  /** Abend kostet dieses Vielfache des Mittags */
  abendFaktor: 2.5,
};

export const NEGATIV = {
  /** Anteil aller Viertelstunden mit negativem Preis, letzte 12 Monate */
  anteilViertelstunden: 6.0,
  /** Anteil der Tage mit mindestens einer negativen Viertelstunde */
  anteilTage: 27,
  tageAbsolut: 96,
  tageGesamt: 356,
  /** Wie lange der Negativpreis an solchen Tagen im Schnitt anhält */
  dauerStunden: 5.3,
  /** Entwicklung des Anteils negativer Viertelstunden je Kalenderjahr */
  trend: [
    { jahr: "2023", anteil: 3.4 },
    { jahr: "2024", anteil: 5.2 },
    { jahr: "2025", anteil: 6.6 },
    { jahr: "2026", anteil: 7.3 },
  ],
};

/**
 * Ein Zeichen je Tag, chronologisch ab 15.08.2025: "1" = an diesem Tag war der
 * Börsenpreis mindestens eine Viertelstunde lang negativ.
 */
export const NEGATIV_TAGE =
  "01100000010000011001001100011111100011000000000000110000000000000000001111001000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000001110000001000110000110010110001000001111110100000011011111111111110000011000001000000111111111000101100000111000011000001100011110100011000001100010011011010100";

/** Monatsanteile negativer Viertelstunden — für die Beschriftung des Streifens. */
export const NEGATIV_MONATE = [
  { label: "Aug", jahr: 2025, anteil: 4.9 },
  { label: "Sep", jahr: 2025, anteil: 8.3 },
  { label: "Okt", jahr: 2025, anteil: 6.7 },
  { label: "Nov", jahr: 2025, anteil: 0.0 },
  { label: "Dez", jahr: 2025, anteil: 0.0 },
  { label: "Jan", jahr: 2026, anteil: 0.3 },
  { label: "Feb", jahr: 2026, anteil: 0.9 },
  { label: "Mär", jahr: 2026, anteil: 4.7 },
  { label: "Apr", jahr: 2026, anteil: 17.1 },
  { label: "Mai", jahr: 2026, anteil: 10.6 },
  { label: "Jun", jahr: 2026, anteil: 6.9 },
  { label: "Jul", jahr: 2026, anteil: 11.0 },
  { label: "Aug", jahr: 2026, anteil: 8.0 },
];

/**
 * Ersparnis aus der Simulation über 12 Monate. Referenzhaushalt: VoltSurfer 30,
 * drei Personen, Wärmepumpe 9 kW, § 14a Modul 1, Vergleich gegen 35 ct/kWh
 * Festpreistarif. Die Zahlen stammen aus zwei identischen Läufen, die sich nur
 * darin unterscheiden, ob der Speicher ins Netz verkaufen darf.
 */
export const ERSPARNIS = {
  /** Mit Netzvermarktung über den Verbund */
  gesamt: 1348,
  /** Ohne Netzverkauf — das entsteht ab dem Tag der Installation */
  heute: 820,
  anteilHeute: 60,
  anteilVerbund: 40,
  amortisation: { mitVerbund: 8, ohneVerbund: 13 },
};

/** Endkundenpreise inkl. Netzentgelt, Umlagen und Steuern — NICHT Börsenpreise. */
export const ENDKUNDE = {
  festpreis: 35,
  abendspitze: 40,
  nachts: 26,
  mittags: 22,
};
